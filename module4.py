import time
import threading
import multiprocessing
import ctypes
import math
import os
 
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
 
# ======================================================================
#  CONSTANTS
# ======================================================================
CACHE_LINE_BYTES = 64
LONG_BYTES       = ctypes.sizeof(ctypes.c_long)   # 8 on 64-bit
PAD_STRIDE       = CACHE_LINE_BYTES // LONG_BYTES  # 8 longs per cache line
 
# Iteration counts - tune ITERS_MAIN so baseline ~1.5-3s on your machine.
# With a multiprocessing.Array, each access goes through a C-extension proxy;
# 1_000_000 iterations should give ~1-2s on most modern machines.
ITERS_MAIN  = 1_000_000   # false sharing & cache-aligned workers
ITERS_TRUE  = 80_000      # true-sharing worker (mutex is extremely slow)
 
PROCESSOR_COUNTS = [1, 2, 4, 8]
 
 
# ======================================================================
#  WORKER FUNCTIONS  (module-level: required by multiprocessing on Windows)
# ======================================================================
 
def _worker_false_sharing(shared_arr, idx, iters):
    """
    False-sharing worker.
 
    shared_arr[idx] is adjacent to other workers' elements on the SAME
    64-byte cache line.  Every += 1 is a read-modify-write that:
      1. Reads  the cache line  (may trigger M->S transition if another
         process recently wrote it)
      2. Modifies the value
      3. Writes  back          (transitions line to M, invalidating all
         other copies via Invalidate bus broadcast -> MESI M->I on others)
 
    This invalidation-refetch cycle happens on EVERY iteration for ALL
    workers sharing the line, producing measurable contention overhead.
    """
    for i in range(iters):
        shared_arr[idx] += 1
 
 
def _worker_true_sharing(shared_val, lock, iters):
    """
    True-sharing worker.
 
    All workers increment the SAME variable under a mutex.
    Only one worker holds the lock at a time; the rest block.
    This is the worst case: O(N) serialisation with N workers.
    """
    for _ in range(iters):
        with lock:
            shared_val.value += 1
 
 
def _worker_padded(shared_arr, idx, stride, iters):
    """
    Cache-aligned (padded) worker.
 
    shared_arr[idx * stride] places each worker's element on its own
    64-byte cache line (stride = PAD_STRIDE = 8 longs = 64 bytes).
 
    Each worker keeps its line in Modified (M) state throughout with no
    forced transitions.  No coherence traffic between workers.
    Performance approaches ideal: time ~ constant regardless of N workers
    (all work in parallel with no sharing overhead).
    """
    actual = idx * stride
    for i in range(iters):
        shared_arr[actual] += 1
 
 
# ======================================================================
#  BENCHMARK RUNNER
# ======================================================================
 
def _run(mode, n, iters):
    """Spawn n multiprocessing.Process workers; return elapsed wall time."""
    if mode == "false":
        arr   = multiprocessing.Array(ctypes.c_long, n, lock=False)
        procs = [
            multiprocessing.Process(
                target=_worker_false_sharing, args=(arr, i, iters))
            for i in range(n)
        ]
    elif mode == "true":
        val  = multiprocessing.Value(ctypes.c_long, 0)
        lock = multiprocessing.Lock()
        procs = [
            multiprocessing.Process(
                target=_worker_true_sharing, args=(val, lock, iters))
            for i in range(n)
        ]
    else:  # padded
        arr   = multiprocessing.Array(ctypes.c_long,
                                      n * PAD_STRIDE, lock=False)
        procs = [
            multiprocessing.Process(
                target=_worker_padded, args=(arr, i, PAD_STRIDE, iters))
            for i in range(n)
        ]
 
    t0 = time.perf_counter()
    for p in procs: p.start()
    for p in procs: p.join()
    return time.perf_counter() - t0
 
 
# ======================================================================
#  MESI STATE TRANSITION DIAGRAM
# ======================================================================
 
def _draw_mesi(ax):
    """
    Render the complete MESI finite-state machine.
    All six canonical transitions are annotated with the bus event that
    triggers them and the MESI state change that results.
    """
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    ax.set_facecolor('#F7F9FC')
 
    # Diamond layout: M top-left, E top-right, S bottom-right, I bottom-left
    pos = {
        'M': (0.22, 0.72),
        'E': (0.72, 0.72),
        'S': (0.72, 0.28),
        'I': (0.22, 0.28),
    }
    colors = {
        'M': '#D62828',   # red
        'E': '#457B9D',   # blue
        'S': '#2A9D8F',   # teal
        'I': '#6C757D',   # grey
    }
    state_labels = {
        'M': 'M\nModified',
        'E': 'E\nExclusive',
        'S': 'S\nShared',
        'I': 'I\nInvalid',
    }
    R = 0.092
 
    # Draw state circles
    for s, (x, y) in pos.items():
        ax.add_patch(plt.Circle(
            (x, y), R, color=colors[s], ec='#1a1a1a', lw=2.2, zorder=5))
        ax.text(x, y, state_labels[s], ha='center', va='center',
                fontsize=9, fontweight='bold', color='white', zorder=6,
                multialignment='center')
 
    def arrow(src, dst, label, rad=0.0, label_shift=(0, 0), fs=7.2):
        """Draw annotated curved arrow from src state to dst state."""
        x1, y1 = pos[src]; x2, y2 = pos[dst]
        dist = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / dist, (y2 - y1) / dist
        # Start/end at circle edge
        xs, ys = x1 + ux * R * 1.10, y1 + uy * R * 1.10
        xe, ye = x2 - ux * R * 1.10, y2 - uy * R * 1.10
 
        ax.annotate('', xy=(xe, ye), xytext=(xs, ys),
                    arrowprops=dict(
                        arrowstyle='->', lw=1.8, color='#1a1a1a',
                        connectionstyle=f'arc3,rad={rad}'),
                    zorder=4)
 
        # Label at arc midpoint
        mx = (xs + xe) / 2 + label_shift[0]
        my = (ys + ye) / 2 + label_shift[1]
        ax.text(mx, my, label, ha='center', va='center', fontsize=fs,
                bbox=dict(boxstyle='round,pad=0.30', fc='#FFFFF0',
                          ec='#AAAAAA', alpha=0.95), zorder=7)
 
    # ── All 6 MESI transitions ────────────────────────────────────────
    # 1. I -> E  Read miss, line not in any cache -> fetch from memory, Exclusive
    arrow('I', 'E',
          'PrRd / BusRd\n(no other copy)\nI \u2192 E',
          rad=-0.30, label_shift=(0.00, 0.14))
 
    # 2. E -> M  Local write to Exclusive line (no bus traffic)
    arrow('E', 'M',
          'PrWr\n(no bus traffic)\nE \u2192 M',
          rad=-0.30, label_shift=(0.00, 0.14))
 
    # 3. M -> I  Remote cache requests line: write-back to memory, then Invalidate
    arrow('M', 'I',
          'BusRd/BusRdX:\nwrite-back + Invalidate\nM \u2192 I',
          rad=-0.30, label_shift=(0.00, -0.14))
 
    # 4. I -> S  Read miss, other caches also hold a copy -> all go Shared
    arrow('I', 'S',
          'PrRd / BusRd\n(others have copy)\nI \u2192 S',
          rad=0.0, label_shift=(0.27, 0.00))
 
    # 5. S -> I  Another cache writes -> broadcasts Invalidate; this copy -> Invalid
    arrow('S', 'I',
          'BusRdX\n(Invalidate rcvd)\nS \u2192 I',
          rad=0.30, label_shift=(0.27, 0.00))
 
    # 6. S -> M  Local write to Shared line: broadcast Invalidate, then Modified
    arrow('S', 'M',
          'PrWr / BusRdX\n(Invalidate bcast)\nS \u2192 M',
          rad=0.0, label_shift=(-0.27, 0.00))
 
    # Legend
    patches = [
        mpatches.Patch(color=colors['M'],
                       label='M \u2014 Modified : dirty, sole owner, memory stale'),
        mpatches.Patch(color=colors['E'],
                       label='E \u2014 Exclusive: clean, sole copy, no bus traffic on write'),
        mpatches.Patch(color=colors['S'],
                       label='S \u2014 Shared   : clean, multiple copies, write needs Invalidate'),
        mpatches.Patch(color=colors['I'],
                       label='I \u2014 Invalid  : stale / absent, next access is a cache miss'),
    ]
    ax.legend(handles=patches, loc='lower center', ncol=2,
              fontsize=7.8, framealpha=0.96, edgecolor='#BBBBBB',
              title='MESI State Definitions', title_fontsize=8.5)
 
    ax.set_title(
        'Figure 4: Complete MESI Cache Coherence State Transition Diagram\n'
        'PrRd/PrWr = Processor Read/Write.  BusRd/BusRdX = Bus Read / Read-Exclusive (with Invalidate)',
        fontsize=9.5, fontweight='bold', pad=8)
 
 
# ======================================================================
#  RESULTS TABLE  (assignment 2.5 / 2.8 format)
# ======================================================================
 
def _draw_table(ax, seq_t, false_times, true_times, pad_times,
                false_overhead, counts):
    """
    Table comparing all three scenarios.
    Primary metric: overhead of false/true sharing vs aligned baseline.
    """
    ax.axis('off')
    ax.set_title(
        'Figure 5: Performance Comparison Table\n'
        '(Overhead = time relative to cache-aligned baseline)',
        fontsize=9.5, fontweight='bold', pad=8)
 
    cols = ['Workers', 'False (s)', 'True (s)', 'Aligned (s)',
            'False\nOverhead', 'True\nOverhead']
    rows = []
    for i, n in enumerate(counts):
        ft_oh = (false_times[i] / pad_times[i] - 1) * 100
        tt_oh = (true_times[i]  / pad_times[i] - 1) * 100
        rows.append([
            str(n),
            f'{false_times[i]:.4f}',
            f'{true_times[i]:.4f}',
            f'{pad_times[i]:.4f}',
            f'+{ft_oh:.1f}%' if ft_oh >= 0 else f'{ft_oh:.1f}%',
            f'+{tt_oh:.1f}%',
        ])
 
    tbl = ax.table(cellText=rows, colLabels=cols,
                   loc='center', cellLoc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    tbl.scale(1, 2.1)
 
    # Header row style
    header_bg = '#3D5A80'
    for j in range(len(cols)):
        tbl[(0, j)].set_facecolor(header_bg)
        tbl[(0, j)].set_text_props(color='white', fontweight='bold')
 
    # Data rows - highlight overhead cells
    for i in range(1, len(rows) + 1):
        base_bg = '#EAF2FB' if i % 2 == 0 else '#FFFFFF'
        for j in range(len(cols)):
            tbl[(i, j)].set_facecolor(base_bg)
        # Colour overhead columns by severity
        ft_oh = (false_times[i-1] / pad_times[i-1] - 1) * 100
        tt_oh = (true_times[i-1]  / pad_times[i-1] - 1) * 100
        # False sharing overhead cell
        fc_f = '#FFD6D6' if ft_oh > 5 else ('#FFFACD' if ft_oh > 0 else '#D6F5D6')
        tbl[(i, 4)].set_facecolor(fc_f)
        # True sharing overhead cell (always high)
        tbl[(i, 5)].set_facecolor('#FFB3B3')
 
 
# ======================================================================
#  MAIN ENTRY POINT
# ======================================================================
 
def run_module_4():
    avail = multiprocessing.cpu_count()
 
    print("\n" + "=" * 85)
    print("MODULE 4: CACHE COHERENCE (MESI PROTOCOL)".center(85))
    print("=" * 85)
    print(f"  System CPUs   : {avail}")
    print(f"  Cache line    : {CACHE_LINE_BYTES} bytes  |  Pad stride: {PAD_STRIDE} longs")
    print(f"  Main iters    : {ITERS_MAIN:,} per worker  (false sharing & padded)")
    print(f"  True iters    : {ITERS_TRUE:,} per worker  (mutex serialised)")
    print(f"  Worker configs: {PROCESSOR_COUNTS}")
    print()
    print("  PRIMARY METRIC: Overhead of false/true sharing vs cache-aligned baseline.")
    print("  (Module 1 measures raw speedup. Module 4 measures cache coherence penalty.)")
    print()
 
    # Sequential baseline
    print("  Measuring baseline (1-process cache-aligned) ...")
    seq_t = _run("padded", 1, ITERS_MAIN)
    print(f"  Baseline : {seq_t:.4f} s\n")
 
    hdr = (f"  {'Workers':<8} | {'False Sh. (s)':<14} | {'True Sh. (s)':<14} | "
           f"{'Aligned (s)':<13} | {'False OH%':<11} | {'True OH%'}")
    print(hdr)
    print("  " + "-" * 85)
 
    false_t, true_t, pad_t = [], [], []
    false_oh, true_oh      = [], []
 
    for n in PROCESSOR_COUNTS:
        ft = _run("false", n, ITERS_MAIN)
        tt = _run("true",  n, ITERS_TRUE)
        pt = seq_t if n == 1 else _run("padded", n, ITERS_MAIN)
 
        false_t.append(ft); true_t.append(tt); pad_t.append(pt)
 
        f_oh = (ft / pt - 1) * 100
        t_oh = (tt / pt - 1) * 100
        false_oh.append(f_oh); true_oh.append(t_oh)
 
        print(f"  {n:<8} | {ft:>11.4f}s  | {tt:>11.4f}s  | {pt:>10.4f}s   | "
              f"{f_oh:>+9.1f}%  | {t_oh:>+.1f}%")
 
    print("  " + "-" * 85)
    print()
    print("  ANALYSIS — Cache Coherence Effects:")
    print()
 
    max_f_oh = max(false_oh)
    max_t_oh = max(true_oh)
    max_n    = PROCESSOR_COUNTS[false_oh.index(max_f_oh)]
 
    print(f"  False Sharing overhead (peak at {max_n} workers): +{max_f_oh:.1f}% slower than aligned.")
    print("  Mechanism: every += 1 on shared_arr[idx] triggers a read-modify-write.")
    print("    Step 1  Cache miss or stale -> BusRd to fetch 64-byte line from memory (I->E or I->S).")
    print("    Step 2  Worker writes -> line transitions to Modified (M).")
    print("    Step 3  Next worker reads same line -> BusRd received by M owner.")
    print("            Owner must write-back to memory, then transition to I (M->I).")
    print("            Requester fetches from memory into E or S state.")
    print("    This M->I write-back + re-fetch cycle repeats on every cross-process write,")
    print("    generating bus traffic proportional to write frequency * worker count.")
    print()
    print(f"  True Sharing overhead (peak at {PROCESSOR_COUNTS[-1]} workers): +{max_t_oh:.1f}% slower than aligned.")
    print("  Mechanism: mutex serialises ALL access. Only 1 worker in critical section at a time.")
    print("    With N workers, N-1 spin-wait while 1 increments -> effective throughput = 1/N.")
    print()
    print("  Cache-Aligned (Padded) baseline:")
    print(f"    PAD_STRIDE = {PAD_STRIDE} longs = {PAD_STRIDE * LONG_BYTES} bytes = 1 cache line per worker.")
    print("    Each worker's element is on its own line -> no Invalidate broadcasts.")
    print("    Each worker's line stays in Modified (M) state: zero coherence bus traffic.")
    print("    Performance does not degrade with worker count for the coherence reason alone.")
    print()
 
    # ── Build graph ───────────────────────────────────────────────────────
    fig = plt.figure(figsize=(20, 13))
    fig.suptitle(
        "Figure 4: Module 4 — Cache Coherence Performance Analysis (MESI Protocol)\n"
        f"False Sharing vs True Sharing (Mutex) vs Cache-Aligned Baseline  "
        f"| {ITERS_MAIN:,} iters/worker",
        fontsize=13, fontweight='bold', y=0.985)
 
    gs = fig.add_gridspec(
        2, 3, hspace=0.42, wspace=0.33,
        top=0.93, bottom=0.04, left=0.06, right=0.97)
 
    ax_t   = fig.add_subplot(gs[0, 0])   # execution time
    ax_oh  = fig.add_subplot(gs[0, 1])   # overhead %
    ax_cmp = fig.add_subplot(gs[0, 2])   # bar comparison at max workers
    ax_m   = fig.add_subplot(gs[1, 0:2]) # MESI diagram (spans 2 cols)
    ax_tbl = fig.add_subplot(gs[1, 2])   # results table
 
    x_lbl = [str(n) for n in PROCESSOR_COUNTS]
 
    # Figure 1: Execution Time
    ax_t.plot(PROCESSOR_COUNTS, false_t, 'o-', color='#E63946', lw=2.2, ms=8,
              label='False Sharing')
    ax_t.plot(PROCESSOR_COUNTS, true_t,  '^-', color='#F4A261', lw=2.2, ms=8,
              label='True Sharing (Mutex)')
    ax_t.plot(PROCESSOR_COUNTS, pad_t,   's-', color='#457B9D', lw=2.2, ms=8,
              label='Cache-Aligned (Padded)')
    ax_t.set_xlabel('Number of Workers')
    ax_t.set_ylabel('Execution Time (seconds)')
    ax_t.set_title('Figure 1: Execution Time vs. Workers\n'
                   '(Lower is better; Aligned should be fastest)')
    ax_t.legend(fontsize=8.5)
    ax_t.grid(True, alpha=0.4)
 
    # Figure 2: Overhead % (false/true vs aligned)
    ax_oh.plot(PROCESSOR_COUNTS, false_oh, 'o-', color='#E63946', lw=2.2, ms=8,
               label='False Sharing overhead %')
    ax_oh.plot(PROCESSOR_COUNTS, true_oh,  '^-', color='#F4A261', lw=2.2, ms=8,
               label='True Sharing overhead %')
    ax_oh.axhline(0, color='#457B9D', lw=1.5, ls='--', label='Aligned baseline (0%)')
    for xv, foh, toh in zip(PROCESSOR_COUNTS, false_oh, true_oh):
        ax_oh.annotate(f'{foh:+.1f}%',
                       xy=(xv, foh), xytext=(xv + 0.1, foh + max(abs(foh), 1) * 0.15),
                       fontsize=7.5, color='#E63946')
    ax_oh.set_xlabel('Number of Workers')
    ax_oh.set_ylabel('Overhead vs Cache-Aligned (%)')
    ax_oh.set_title('Figure 2: False / True Sharing Overhead\n'
                    'vs Cache-Aligned Baseline (%)')
    ax_oh.legend(fontsize=8)
    ax_oh.grid(True, alpha=0.4)
 
    # Figure 3: Grouped bar comparison at max worker count
    n_max = PROCESSOR_COUNTS[-1]
    categories = ['False\nSharing', 'True Sharing\n(Mutex)', 'Cache-Aligned\n(Padded)']
    times_max  = [false_t[-1], true_t[-1], pad_t[-1]]
    bar_colors = ['#E63946', '#F4A261', '#457B9D']
    bars = ax_cmp.bar(categories, times_max, color=bar_colors,
                      edgecolor='black', lw=0.9)
    for bar, val in zip(bars, times_max):
        ax_cmp.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(times_max) * 0.015,
                    f'{val:.3f}s', ha='center', va='bottom',
                    fontsize=9, fontweight='bold')
    ax_cmp.set_ylabel('Execution Time (s)')
    ax_cmp.set_title(f'Figure 3: Scenario Comparison\nat {n_max} Workers (lower = better)')
    ax_cmp.grid(True, axis='y', alpha=0.4)
 
    # Figure 4: MESI State Transition Diagram
    _draw_mesi(ax_m)
 
    # Figure 5: Results Table
    _draw_table(ax_tbl, seq_t, false_t, true_t, pad_t, false_oh, PROCESSOR_COUNTS)
 
    # Display Plot
    try:
        fig.canvas.manager.window.attributes('-topmost', 1)
        fig.canvas.manager.window.attributes('-topmost', 0)
    except:
        pass
    plt.show()
    print("  Module 4 complete.\n")
 