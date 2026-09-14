import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
import streamlit as st

st.set_page_config(page_title="Mines Strategy Simulator", page_icon="💣", layout="wide")

plt.rcParams.update({
    "figure.facecolor":  "#0e1117",
    "axes.facecolor":    "#0e1117",
    "savefig.facecolor": "#0e1117",
    "axes.edgecolor":    "#2a2f3a",
    "axes.labelcolor":   "#e6e6e6",
    "axes.titlecolor":   "#ffffff",
    "axes.titleweight":  "bold",
    "axes.titlesize":    14,
    "axes.labelsize":    11,
    "xtick.color":       "#b8b8b8",
    "ytick.color":       "#b8b8b8",
    "grid.color":        "#2a2f3a",
    "grid.linestyle":    "--",
    "grid.alpha":        0.5,
    "legend.facecolor":  "#161a23",
    "legend.edgecolor":  "#2a2f3a",
    "legend.labelcolor": "#e6e6e6",
    "font.family":       "DejaVu Sans",
})

PROFIT_COLOR = "#22c55e"   # green
LOSS_COLOR   = "#ef4444"   # red (covers both in-loss and blown)
BLOWN_COLOR  = "#ef4444"   # red (kept as alias)
ACCENT       = "#38bdf8"   # sky blue
BASELINE     = "#e5e7eb"   # near white

st.title("💣 Mines Strategy Simulator")
st.caption(
    "Disclaimer: On gambling sites the house edge isn't constant "
    "(it's ~3.5% on average for 4–5 mines with 3–4 tile reveals). "
    "Try using fewer mines and reveals to get a more accurate result."
)

with st.sidebar:
    st.header("Parameters")
    tiles_h = st.number_input("Tiles horizontally", min_value=2, max_value=20, value=5, step=1)
    tiles_v = st.number_input("Tiles vertically",   min_value=2, max_value=20, value=5, step=1)
    total_tiles = int(tiles_h * tiles_v)

    n_mines = st.number_input("Number of mines", min_value=1, max_value=total_tiles - 1, value=5, step=1)
    opened  = st.number_input("Tiles to reveal", min_value=1, max_value=total_tiles - int(n_mines), value=3, step=1)

    house_edge = st.slider("House edge", 0.0, 0.20, 0.035, 0.005, format="%.3f")

    starting_balance = st.number_input("Starting balance", min_value=1.0, value=1000.0, step=10.0)
    bet_size         = st.number_input("Bet size",         min_value=0.01, value=10.0,  step=1.0)
    n_plays          = st.number_input("Plays per simulation", min_value=1, value=100, step=10)
    n_simulation     = st.number_input("Number of simulations", min_value=1, max_value=5000, value=200, step=10)
    martingale       = st.checkbox("Use martingale", value=False)

    run = st.button("▶ Run simulation", type="primary", use_container_width=True)


def mines_round(total_t: int, total_m: int, n_open: int):
    p_win = 1.0
    for i in range(n_open):
        p_win *= (total_t - total_m - i) / (total_t - i)
    return np.random.rand() > p_win, p_win


def simulate(balance, bet_amount, n_bets, total_t, total_m, n_open, edge, use_mart):
    bal = balance
    current_bet = bet_amount
    xs, ys = [0], [bal]
    for n in range(1, n_bets + 1):
        if bal < current_bet or bal <= 0:
            break
        lost, p_win = mines_round(total_t, total_m, n_open)
        multi = (1 / p_win) * (1 - edge)
        if not lost:
            bal += current_bet * (multi - 1)
            if use_mart:
                current_bet = bet_amount
        else:
            bal -= current_bet
            if use_mart and current_bet * 2 <= bal:
                current_bet *= 2
            else:
                current_bet = bet_amount
        current_bet = min(current_bet, bal)
        xs.append(n)
        ys.append(bal)
    return xs, ys, bal


if run:
    profitable = blown = 0
    final_balances = []
    all_runs = []

    progress = st.progress(0.0)

    for s in range(int(n_simulation)):
        xs, ys, final_bal = simulate(
            starting_balance, bet_size, int(n_plays),
            total_tiles, int(n_mines), int(opened),
            house_edge, martingale,
        )
        all_runs.append((xs, ys, final_bal))
        final_balances.append(final_bal)
        if final_bal <= 0:
            blown += 1
        elif final_bal > starting_balance:
            profitable += 1
        progress.progress((s + 1) / n_simulation)

    pct_prof  = profitable / n_simulation * 100
    pct_blown = blown / n_simulation * 100
    pct_loss  = 100 - pct_prof - pct_blown

    # ---------------- Metrics (with elevated card styling) ----------------
    st.markdown(
        """
        <style>
        div[data-testid="stMetric"] {
            background: linear-gradient(145deg, #161a23 0%, #11141b 100%);
            border: 1px solid #2a2f3a;
            border-radius: 14px;
            padding: 18px 20px;
            box-shadow:
                0 10px 25px -10px rgba(0, 0, 0, 0.7),
                0 4px 10px -4px rgba(56, 189, 248, 0.08),
                inset 0 1px 0 rgba(255, 255, 255, 0.04);
            transition: transform .15s ease, box-shadow .15s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow:
                0 14px 30px -10px rgba(0, 0, 0, 0.8),
                0 6px 14px -4px rgba(56, 189, 248, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.06);
        }
        div[data-testid="stMetricLabel"] p {
            color: #b8b8b8 !important;
            font-size: 0.85rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        div[data-testid="stMetricValue"] {
            color: #ffffff !important;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Profitable",        f"{pct_prof:.1f}%")
    c2.metric("Blown",             f"{pct_blown:.1f}%")
    c3.metric("In loss",           f"{pct_loss:.1f}%")
    c4.metric("Avg final balance", f"{np.mean(final_balances):.2f}")

    # ---------------- Balance over time (full width) ----------------
    st.subheader("Balance trajectories")
    fig, ax = plt.subplots(figsize=(14, 6), dpi=120)
    for xs, ys, final_bal in all_runs:
        color = PROFIT_COLOR if final_bal > starting_balance else LOSS_COLOR
        ax.plot(xs, ys, linewidth=1.6, alpha=0.45, color=color)

    ax.axhline(starting_balance, color=BASELINE, linestyle="--",
               linewidth=1.5, label="Starting balance", alpha=0.9)
    ax.set_xlabel("Number of Bet")
    ax.set_ylabel("Balance")
    ax.set_title("Balance trajectories across simulations")
    ax.grid(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    from matplotlib.lines import Line2D
    legend_items = [
        Line2D([0], [0], color=PROFIT_COLOR, lw=2, label="Profit"),
        Line2D([0], [0], color=LOSS_COLOR,   lw=2, label="Loss"),
        Line2D([0], [0], color=BASELINE, lw=1.2, linestyle="--", label="Starting balance"),
    ]
    ax.legend(handles=legend_items, loc="best", frameon=True)
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

    # ---------------- Final balance distribution (full width) ----------------
    st.subheader("Final balance distribution")
    fig2, ax2 = plt.subplots(figsize=(14, 5.5), dpi=120)

    final_arr = np.array(final_balances)
    n, bins, patches = ax2.hist(final_arr, bins=40, edgecolor="#0e1117", linewidth=0.6)

    for patch, left_edge in zip(patches, bins[:-1]):
        center = left_edge + (bins[1] - bins[0]) / 2
        patch.set_facecolor(PROFIT_COLOR if center > starting_balance else LOSS_COLOR)
        patch.set_alpha(0.9)

    ax2.axvline(starting_balance, color=BASELINE, linestyle="--",
                linewidth=1.2, label=f"Start ({starting_balance:.0f})")
    ax2.axvline(float(np.mean(final_arr)), color=ACCENT, linestyle="-",
                linewidth=1.5, label=f"Mean ({np.mean(final_arr):.0f})")

    ax2.set_xlabel("Final balance")
    ax2.set_ylabel("Simulations")
    ax2.grid(True, axis="y")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.legend(loc="best", frameon=True)
    fig2.tight_layout()
    st.pyplot(fig2, clear_figure=True)

    # ---------------- Win probability vs. tiles opened (full width) ----------------
    st.subheader("Win probability vs. tiles opened")

    def hypergeometric_pmf(k, N, K, n):
        if k < 0 or k > K or n < 0 or n > N:
            return 0.0
        from math import comb
        return (comb(K, k) * comb(N - K, n - k)) / comb(N, n)

    N = total_tiles
    K = int(n_mines)
    Xs = list(range(1, N - K + 1))
    Ys = [hypergeometric_pmf(0, N, K, i) for i in Xs]

    win_cmap = mcolors.LinearSegmentedColormap.from_list("win_prob", [LOSS_COLOR, PROFIT_COLOR])
    bar_colors = [win_cmap(y) for y in Ys]

    fig3, ax3 = plt.subplots(figsize=(14, 5.5), dpi=120)
    bars = ax3.bar(Xs, Ys, color=bar_colors, edgecolor="#0e1117", linewidth=0.6)

    selected = int(opened)
    if 1 <= selected <= len(Xs):
        bars[selected - 1].set_edgecolor(ACCENT)
        bars[selected - 1].set_linewidth(2.2)

    from matplotlib.ticker import MaxNLocator
    ax3.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax3.set_xlabel("# of tiles opened")
    ax3.set_ylabel("Probability of winning")
    ax3.set_title("Win probability by number of tiles revealed")
    ax3.set_ylim(0, 1)
    ax3.grid(True, axis="y")
    ax3.spines["top"].set_visible(False)
    ax3.spines["right"].set_visible(False)

    legend_items = [
        Line2D([0], [0], marker="s", color="none", markerfacecolor=PROFIT_COLOR,
               markersize=10, label="Higher win probability"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor=LOSS_COLOR,
               markersize=10, label="Lower win probability"),
        Line2D([0], [0], color=ACCENT, lw=2.2, label=f"Your setting ({selected})"),
    ]
    ax3.legend(handles=legend_items, loc="best", frameon=True)
    fig3.tight_layout()
    st.pyplot(fig3, clear_figure=True)
else:
    st.info("Set your parameters in the sidebar, then click **Run simulation**.")


