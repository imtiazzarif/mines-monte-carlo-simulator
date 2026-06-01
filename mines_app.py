import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="Mines Strategy Simulator", page_icon="💣", layout="wide")

st.title("💣 Mines Strategy Simulator")
st.caption(
    "Disclaimer: On gambling sites the house edge isn't constant "
    "(it's ~3.5% on average for 4–5 mines with 3–4 tile reveals). "
    "Try using fewer mines and reveals to get a more accurate result."
)

# ---------------- Sidebar inputs ----------------
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

    fig, ax = plt.subplots(figsize=(10, 5))
    progress = st.progress(0.0)

    for s in range(int(n_simulation)):
        xs, ys, final_bal = simulate(
            starting_balance, bet_size, int(n_plays),
            total_tiles, int(n_mines), int(opened),
            house_edge, martingale,
        )
        ax.plot(xs, ys, linewidth=0.6, alpha=0.6)
        final_balances.append(final_bal)
        if final_bal <= 0:
            blown += 1
        elif final_bal > starting_balance:
            profitable += 1
        progress.progress((s + 1) / n_simulation)

    ax.axhline(starting_balance, color="black", linestyle="--", linewidth=1, label="Starting balance")
    ax.set_xlabel("Bet #")
    ax.set_ylabel("Balance")
    ax.set_title("Balance over time across simulations")
    ax.legend(loc="best")

    pct_prof = profitable / n_simulation * 100
    pct_blown = blown / n_simulation * 100
    pct_loss  = 100 - pct_prof - pct_blown

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Profitable", f"{pct_prof:.1f}%")
    c2.metric("Blown",      f"{pct_blown:.1f}%")
    c3.metric("In loss",    f"{pct_loss:.1f}%")
    c4.metric("Avg final balance", f"{np.mean(final_balances):.2f}")

    st.pyplot(fig, clear_figure=True)

    st.subheader("Final balance distribution")
    fig2, ax2 = plt.subplots(figsize=(10, 3))
    ax2.hist(final_balances, bins=40)
    ax2.axvline(starting_balance, color="black", linestyle="--", linewidth=1)
    ax2.set_xlabel("Final balance")
    ax2.set_ylabel("Simulations")
    st.pyplot(fig2, clear_figure=True)
else:
    st.info("Set your parameters in the sidebar, then click **Run simulation**.")
