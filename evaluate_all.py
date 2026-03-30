import os
import sys
import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Patch
from stable_baselines3 import PPO, A2C, DQN
from rts_env import RTSEnv, N_ACTIONS
from units import Heavy, Light, Ranged, Worker
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))
                if "__file__" in dir() else os.getcwd())


N_EPISODES = 1000

PPO_PATH = "rts_ppo_model"
A2C_PATH = "rts_a2c_model"
DQN_PATH = "rts_dqn_model"

USE_BEST = False

OUT_COMPARISON = "evaluation_comparison.png"
OUT_TXT        = "evaluation_report.txt"

# Светлые цвета для графиков
BLUE_WIN  = "#2c7bb6"      # темно-синий для побед
RED_WIN   = "#d7191c"      # ярко-красный для поражений
DRAW_COL  = "#abd9e9"      # светло-голубой для ничьих
ACCENT    = "#fdae61"      # оранжевый акцент

ALGO_COLORS = {
    "PPO": "#2c7bb6",       # синий
    "A2C": "#2ca02c",       # зеленый
    "DQN": "#d95f02",       # оранжевый
}

# Светлая тема
BG_DARK  = "#ffffff"        # белый фон
BG_PANEL = "#f8f9fa"        # очень светлый серый для панелей
GRID_C   = "#dee2e6"        # светлый серый для сетки
TEXT_C   = "#212529"        # темно-серый для текста


def run_episode(env: RTSEnv, model, seed: int) -> dict:
    obs, _ = env.reset(seed=seed)
    g = env.game
    total_reward         = 0.0
    action_counts        = [0] * N_ACTIONS
    rewards_per_step     = []
    blue_units_history   = []
    red_units_history    = []
    minerals_history     = []

    while True:
        action, _ = model.predict(obs, deterministic=True)
        action_counts[int(action)] += 1
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        rewards_per_step.append(reward)
        g = env.game
        blue_units_history.append(len([u for u in g.units if u.player == 'blue']))
        red_units_history.append(len([u for u in g.units if u.player == 'red']))
        minerals_history.append(g.player_resources['blue']['minerals'])
        if terminated or truncated:
            break

    winner    = info.get("winner") or "draw"
    turns     = len(rewards_per_step)
    blue_units = [u for u in g.units if u.player == 'blue']
    blue_blds  = [b for b in g.buildings if b.player == 'blue']

    return dict(
        seed                 = seed,
        winner               = winner,
        total_reward         = total_reward,
        turns                = turns,
        action_counts        = action_counts,
        rewards_per_step     = rewards_per_step,
        blue_units_history   = blue_units_history,
        red_units_history    = red_units_history,
        minerals_history     = minerals_history,
        final_blue_units     = len(blue_units),
        final_blue_buildings = len(blue_blds),
        workers  = sum(1 for u in blue_units if isinstance(u, Worker)),
        lights   = sum(1 for u in blue_units if isinstance(u, Light)),
        heavies  = sum(1 for u in blue_units if isinstance(u, Heavy)),
        ranged   = sum(1 for u in blue_units if isinstance(u, Ranged)),
    )


def evaluate(model, n_episodes: int, algo_name: str) -> list:
    env = RTSEnv()
    results = []
    print(f"\n{algo_name}")
    for i in range(n_episodes):
        seed = random.randint(0, 10**7)
        ep   = run_episode(env, model, seed)
        results.append(ep)
        if (i + 1) % 10 == 0:
            wins   = sum(1 for r in results if r['winner'] == 'blue')
            losses = sum(1 for r in results if r['winner'] == 'red')
            draws  = sum(1 for r in results if r['winner'] == 'draw')
            mean_r = np.mean([r['total_reward'] for r in results])
            print(
                f"  [{i+1:>4}/{n_episodes}]  "
                f"W={wins}  L={losses}  D={draws}  "
                f"mean_reward={mean_r:+.2f}"
            )
    env.close()
    return results


def style_ax(ax, title):
    ax.set_facecolor(BG_PANEL)
    ax.set_title(title, color=TEXT_C, fontsize=11, pad=6)
    ax.tick_params(colors=TEXT_C)
    for spine in ax.spines.values():
        spine.set_color(GRID_C)
    ax.xaxis.label.set_color(TEXT_C)
    ax.yaxis.label.set_color(TEXT_C)
    ax.grid(color=GRID_C, linestyle="--", linewidth=0.5, alpha=0.7)


def build_single_chart(results: list, algo_name: str, out_path: str):
    n      = len(results)
    wins   = [r for r in results if r['winner'] == 'blue']
    losses = [r for r in results if r['winner'] == 'red']
    draws  = [r for r in results if r['winner'] == 'draw']

    rewards    = [r['total_reward'] for r in results]
    turns_list = [r['turns']        for r in results]
    win_flags  = [1 if r['winner'] == 'blue' else 0 for r in results]
    win_ma     = np.convolve(win_flags, np.ones(10) / 10, mode='valid')

    action_total = np.zeros(N_ACTIONS, dtype=int)
    for r in results:
        action_total += np.array(r['action_counts'])

    algo_color = ALGO_COLORS.get(algo_name, BLUE_WIN)

    fig = plt.figure(figsize=(20, 22), facecolor=BG_DARK)
    fig.suptitle(
        f"Оценка модели {algo_name} · {n} партий   "
        f"Победы: {len(wins)} ({100*len(wins)/n:.1f}%)  "
        f"Поражения: {len(losses)} ({100*len(losses)/n:.1f}%)  "
        f"Ничьи: {len(draws)} ({100*len(draws)/n:.1f}%)",
        fontsize=15, color=TEXT_C, y=0.98,
    )

    gs = gridspec.GridSpec(4, 3, figure=fig, hspace=0.45, wspace=0.35)

    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor(BG_PANEL)
    wedges, texts, autotexts = ax1.pie(
        [len(wins), len(losses), len(draws)],
        labels=[f"Победа\n{len(wins)}", f"Поражение\n{len(losses)}", f"Ничья\n{len(draws)}"],
        colors=[algo_color, RED_WIN, DRAW_COL],
        autopct="%1.1f%%", startangle=90,
        textprops={"color": TEXT_C, "fontsize": 10},
        wedgeprops={"edgecolor": BG_DARK, "linewidth": 2},
    )
    for at in autotexts:
        at.set_color(TEXT_C); at.set_fontsize(9)
    ax1.set_title(f"Исходы — {algo_name}", color=TEXT_C, fontsize=11, pad=6)

    ax2 = fig.add_subplot(gs[0, 1:])
    style_ax(ax2, "Суммарная награда по партиям")
    c_scatter = [algo_color if r['winner'] == 'blue' else
                 RED_WIN  if r['winner'] == 'red' else DRAW_COL
                 for r in results]
    ax2.scatter(range(n), rewards, c=c_scatter, s=18, alpha=0.7)
    ma = np.convolve(rewards, np.ones(10) / 10, mode='valid')
    ax2.plot(range(9, n), ma, color=ACCENT, linewidth=2, label="MA-10")
    ax2.axhline(np.mean(rewards), color=TEXT_C, linestyle="--", linewidth=1,
                label=f"Среднее: {np.mean(rewards):+.2f}")
    ax2.set_xlabel("Партия №"); ax2.set_ylabel("Суммарная награда")
    legend_patches = [Patch(color=algo_color, label="Победа"),
                      Patch(color=RED_WIN,    label="Поражение"),
                      Patch(color=DRAW_COL,   label="Ничья")]
    ax2.legend(handles=legend_patches + ax2.get_legend_handles_labels()[0][2:],
               facecolor=BG_PANEL, edgecolor=GRID_C, labelcolor=TEXT_C, fontsize=9)

    ax3 = fig.add_subplot(gs[1, :2])
    style_ax(ax3, "Скользящий % побед (окно = 10 партий)")
    ax3.fill_between(range(9, n), win_ma * 100, alpha=0.3, color=algo_color)
    ax3.plot(range(9, n), win_ma * 100, color=algo_color, linewidth=2)
    ax3.axhline(100 * len(wins) / n, color=ACCENT, linestyle="--", linewidth=1.2,
                label=f"Общий % побед: {100*len(wins)/n:.1f}%")
    ax3.set_ylim(0, 100); ax3.set_xlabel("Партия №"); ax3.set_ylabel("% побед")
    ax3.legend(facecolor=BG_PANEL, edgecolor=GRID_C, labelcolor=TEXT_C, fontsize=9)

    ax4 = fig.add_subplot(gs[1, 2])
    style_ax(ax4, "Длина партий (ходов)")
    ax4.hist(turns_list, bins=20, color=ACCENT, edgecolor=BG_DARK, alpha=0.85)
    ax4.axvline(np.mean(turns_list), color=TEXT_C, linestyle="--", linewidth=1.5,
                label=f"Среднее: {np.mean(turns_list):.1f}")
    ax4.set_xlabel("Ходов"); ax4.set_ylabel("Кол-во партий")
    ax4.legend(facecolor=BG_PANEL, edgecolor=GRID_C, labelcolor=TEXT_C, fontsize=9)

    ax5 = fig.add_subplot(gs[2, 0])
    style_ax(ax5, "Гистограмма наград")
    if len(rewards) > 1:
        bins = np.linspace(min(rewards), max(rewards), 25)
    else:
        bins = 25
    ax5.hist([r['total_reward'] for r in wins],   bins=bins, color=algo_color, alpha=0.7, label="Победа")
    ax5.hist([r['total_reward'] for r in losses], bins=bins, color=RED_WIN,   alpha=0.7, label="Поражение")
    ax5.hist([r['total_reward'] for r in draws],  bins=bins, color=DRAW_COL,  alpha=0.7, label="Ничья")
    ax5.set_xlabel("Суммарная награда"); ax5.set_ylabel("Кол-во партий")
    ax5.legend(facecolor=BG_PANEL, edgecolor=GRID_C, labelcolor=TEXT_C, fontsize=8)

    ax7 = fig.add_subplot(gs[3, 0])
    ax7.set_facecolor(BG_PANEL); ax7.axis("off")
    reward_w = [r['total_reward'] for r in wins]   or [0]
    reward_l = [r['total_reward'] for r in losses] or [0]
    reward_d = [r['total_reward'] for r in draws]  or [0]
    turns_w  = [r['turns'] for r in wins]   or [0]
    turns_l  = [r['turns'] for r in losses] or [0]
    lines = [
        ("Алгоритм",                   algo_name),
        ("Партий сыграно",             f"{n}"),
        ("Побед / Поражений / Ничей",  f"{len(wins)} / {len(losses)} / {len(draws)}"),
        ("Победность",                 f"{100*len(wins)/n:.1f}%"),
        ("──────────────────────",     ""),
        ("Средняя награда (все)",      f"{np.mean(rewards):+.3f}"),
        ("  при победе",               f"{np.mean(reward_w):+.3f}"),
        ("  при поражении",            f"{np.mean(reward_l):+.3f}"),
        ("  при ничьей",               f"{np.mean(reward_d):+.3f}"),
        ("──────────────────────",     ""),
        ("Средняя длина (все)",        f"{np.mean(turns_list):.1f} ходов"),
        ("  при победе",               f"{np.mean(turns_w):.1f}"),
        ("  при поражении",            f"{np.mean(turns_l):.1f}"),
        ("──────────────────────",     ""),
        ("Std награды",                f"{np.std(rewards):.3f}"),
        ("Min / Max награды",          f"{min(rewards):+.2f} / {max(rewards):+.2f}"),
    ]
    y = 0.97
    for label, val in lines:
        ax7.text(0.02, y, label, transform=ax7.transAxes,
                 color="#495057", fontsize=9, va="top")
        ax7.text(0.72, y, val,   transform=ax7.transAxes,
                 color=TEXT_C,   fontsize=9, va="top", ha="right")
        y -= 0.062
    ax7.set_title("Сводная статистика", color=TEXT_C, fontsize=11, pad=6)

    ax8 = fig.add_subplot(gs[3, 1])
    style_ax(ax8, "Стабильность: ящики по блокам из 20 партий")
    block = max(1, n // 5)
    boxes_data = [rewards[i*block:(i+1)*block] for i in range(5)]
    boxes_data = [b for b in boxes_data if b]
    labels_box = [f"{i*block+1}–{min((i+1)*block, n)}" for i in range(len(boxes_data))]
    bp = ax8.boxplot(
        boxes_data, labels=labels_box, patch_artist=True,
        medianprops=dict(color=ACCENT, linewidth=2),
        whiskerprops=dict(color=TEXT_C), capprops=dict(color=TEXT_C),
        flierprops=dict(markerfacecolor=RED_WIN, marker="o", markersize=3, alpha=0.5),
    )
    for patch in bp["boxes"]:
        patch.set_facecolor(algo_color); patch.set_alpha(0.5)
    ax8.set_xlabel("Блок партий"); ax8.set_ylabel("Суммарная награда")

    ax9 = fig.add_subplot(gs[3, 2])
    style_ax(ax9, "Победность по блокам из 20 партий")
    win_pct_blocks = []
    for i in range(len(boxes_data)):
        br = results[i*block:(i+1)*block]
        win_pct_blocks.append(100 * sum(1 for r in br if r['winner'] == 'blue') / len(br))
    ax9.bar(range(len(win_pct_blocks)), win_pct_blocks,
            color=algo_color, alpha=0.8, edgecolor=BG_DARK)
    ax9.axhline(100 * len(wins) / n, color=ACCENT, linestyle="--", linewidth=1.2,
                label=f"Среднее: {100*len(wins)/n:.1f}%")
    ax9.set_xticks(list(range(len(win_pct_blocks))))
    ax9.set_xticklabels(labels_box, fontsize=8)
    ax9.set_ylim(0, 100); ax9.set_ylabel("% побед"); ax9.set_xlabel("Блок партий")
    ax9.legend(facecolor=BG_PANEL, edgecolor=GRID_C, labelcolor=TEXT_C, fontsize=9)

    plt.savefig(out_path, dpi=130, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"✓ Индивидуальный отчёт {algo_name}: {out_path}")


def build_comparison_chart(all_results: dict, out_path: str):
    algos = list(all_results.keys())
    n     = len(next(iter(all_results.values())))

    fig = plt.figure(figsize=(22, 18), facecolor=BG_DARK)
    fig.suptitle(
        f"Сравнение алгоритмов: {' vs '.join(algos)}  ·  {n} партий каждый",
        fontsize=16, color=TEXT_C, y=0.99,
    )
    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

    for col, algo in enumerate(algos):
        results = all_results[algo]
        wins   = sum(1 for r in results if r['winner'] == 'blue')
        losses = sum(1 for r in results if r['winner'] == 'red')
        draws  = sum(1 for r in results if r['winner'] == 'draw')
        ax = fig.add_subplot(gs[0, col])
        ax.set_facecolor(BG_PANEL)
        algo_col = ALGO_COLORS[algo]
        wedges, texts, autotexts = ax.pie(
            [wins, losses, draws],
            labels=[f"Победа\n{wins}", f"Поражение\n{losses}", f"Ничья\n{draws}"],
            colors=[algo_col, RED_WIN, DRAW_COL],
            autopct="%1.1f%%", startangle=90,
            textprops={"color": TEXT_C, "fontsize": 9},
            wedgeprops={"edgecolor": BG_DARK, "linewidth": 2},
        )
        for at in autotexts:
            at.set_color(TEXT_C); at.set_fontsize(8)
        ax.set_title(f"{algo}  ({100*wins/n:.1f}% побед)", color=algo_col,
                     fontsize=12, pad=6, fontweight="bold")

    ax2 = fig.add_subplot(gs[1, :2])
    style_ax(ax2, "Скользящий % побед (окно = 10 партий)")
    for algo in algos:
        results   = all_results[algo]
        win_flags = [1 if r['winner'] == 'blue' else 0 for r in results]
        win_ma    = np.convolve(win_flags, np.ones(10) / 10, mode='valid')
        ax2.plot(range(9, n), win_ma * 100,
                 color=ALGO_COLORS[algo], linewidth=2, label=algo)
        ax2.fill_between(range(9, n), win_ma * 100, alpha=0.1, color=ALGO_COLORS[algo])
    ax2.set_ylim(0, 100)
    ax2.set_xlabel("Партия №"); ax2.set_ylabel("% побед")
    ax2.legend(facecolor=BG_PANEL, edgecolor=GRID_C, labelcolor=TEXT_C, fontsize=10)

    ax3 = fig.add_subplot(gs[1, 2])
    style_ax(ax3, "Распределение суммарных наград")
    box_data = [[r['total_reward'] for r in all_results[a]] for a in algos]
    bp = ax3.boxplot(
        box_data, labels=algos, patch_artist=True,
        medianprops=dict(color=ACCENT, linewidth=2.5),
        whiskerprops=dict(color=TEXT_C), capprops=dict(color=TEXT_C),
        flierprops=dict(markerfacecolor=RED_WIN, marker="o", markersize=3, alpha=0.5),
    )
    for patch, algo in zip(bp["boxes"], algos):
        patch.set_facecolor(ALGO_COLORS[algo]); patch.set_alpha(0.6)
    ax3.set_ylabel("Суммарная награда")

    ax4 = fig.add_subplot(gs[2, 0])
    style_ax(ax4, "Итоговая статистика исходов")
    x       = np.arange(len(algos))
    width   = 0.25
    win_pct = [100 * sum(1 for r in all_results[a] if r['winner'] == 'blue') / n for a in algos]
    los_pct = [100 * sum(1 for r in all_results[a] if r['winner'] == 'red')  / n for a in algos]
    drw_pct = [100 * sum(1 for r in all_results[a] if r['winner'] == 'draw') / n for a in algos]
    ax4.bar(x - width, win_pct, width, color=[ALGO_COLORS[a] for a in algos], label="Победа",    alpha=0.85)
    ax4.bar(x,         los_pct, width, color=RED_WIN,  label="Поражение", alpha=0.7)
    ax4.bar(x + width, drw_pct, width, color=DRAW_COL, label="Ничья",     alpha=0.7)
    ax4.set_xticks(x); ax4.set_xticklabels(algos)
    ax4.set_ylabel("%"); ax4.set_ylim(0, 100)
    ax4.legend(facecolor=BG_PANEL, edgecolor=GRID_C, labelcolor=TEXT_C, fontsize=9)
    for i, (a, b, c) in enumerate(zip(win_pct, los_pct, drw_pct)):
        ax4.text(i - width, a + 1, f"{a:.0f}%", ha="center", color=TEXT_C, fontsize=8)
        ax4.text(i,         b + 1, f"{b:.0f}%", ha="center", color=TEXT_C, fontsize=8)
        ax4.text(i + width, c + 1, f"{c:.0f}%", ha="center", color=TEXT_C, fontsize=8)

    ax5 = fig.add_subplot(gs[2, 1])
    style_ax(ax5, "Средняя длина партии (ходов)")
    means = [np.mean([r['turns'] for r in all_results[a]]) for a in algos]
    stds  = [np.std( [r['turns'] for r in all_results[a]]) for a in algos]
    bars  = ax5.bar(algos, means, color=[ALGO_COLORS[a] for a in algos],
                    yerr=stds, capsize=5, alpha=0.85, edgecolor=BG_DARK,
                    error_kw=dict(ecolor=TEXT_C, elinewidth=1.5))
    for bar, m in zip(bars, means):
        ax5.text(bar.get_x() + bar.get_width() / 2, m + 0.5,
                 f"{m:.1f}", ha="center", color=TEXT_C, fontsize=10, fontweight="bold")
    ax5.set_ylabel("Ходов")

    ax6 = fig.add_subplot(gs[2, 2])
    ax6.set_facecolor(BG_PANEL); ax6.axis("off")
    ax6.set_title("Сводная таблица", color=TEXT_C, fontsize=11, pad=6)

    headers = ["Метрика"] + algos
    col_w   = [0.38] + [0.20] * len(algos)
    y0 = 0.95
    dy = 0.082

    x_pos = 0.02
    for h, w in zip(headers, col_w):
        ax6.text(x_pos, y0, h, transform=ax6.transAxes,
                 color="#2c7bb6", fontsize=9, va="top", fontweight="bold")
        x_pos += w
    y0 -= dy

    def row(label, vals):
        nonlocal y0
        x_pos = 0.02
        ax6.text(x_pos, y0, label, transform=ax6.transAxes,
                 color="#495057", fontsize=8, va="top")
        x_pos += col_w[0]
        for v, algo in zip(vals, algos):
            ax6.text(x_pos, y0, str(v), transform=ax6.transAxes,
                     color=ALGO_COLORS[algo], fontsize=8, va="top")
            x_pos += 0.20
        y0 -= dy

    row("Победность, %",
        [f"{100*sum(1 for r in all_results[a] if r['winner']=='blue')/n:.1f}" for a in algos])
    row("Ср. награда",
        [f"{np.mean([r['total_reward'] for r in all_results[a]]):+.2f}" for a in algos])
    row("Std награды",
        [f"{np.std([r['total_reward'] for r in all_results[a]]):.2f}" for a in algos])
    row("Ср. длина, ходов",
        [f"{np.mean([r['turns'] for r in all_results[a]]):.1f}" for a in algos])
    row("Мин. награда",
        [f"{min(r['total_reward'] for r in all_results[a]):+.2f}" for a in algos])
    row("Макс. награда",
        [f"{max(r['total_reward'] for r in all_results[a]):+.2f}" for a in algos])

    plt.savefig(out_path, dpi=130, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def load_model(algo_cls, path: str, log_dir: str, use_best: bool):
    if use_best:
        best = os.path.join(log_dir, "best_model.zip")
        if os.path.exists(best):
            return algo_cls.load(best)
    full_path = path + ".zip" if not path.endswith(".zip") else path
    if os.path.exists(full_path):
        return algo_cls.load(full_path)
    return None


def run_evaluation(
    n_episodes   = None,
    ppo_path     = None,
    a2c_path     = None,
    dqn_path     = None,
    use_best     = None,
    out_compare  = None,
    out_txt      = None,
):
    n_episodes  = n_episodes  if n_episodes  is not None else N_EPISODES
    ppo_path    = ppo_path    if ppo_path    is not None else PPO_PATH
    a2c_path    = a2c_path    if a2c_path    is not None else A2C_PATH
    dqn_path    = dqn_path    if dqn_path    is not None else DQN_PATH
    use_best    = use_best    if use_best    is not None else USE_BEST
    out_compare = out_compare if out_compare is not None else OUT_COMPARISON
    out_txt     = out_txt     if out_txt     is not None else OUT_TXT

    configs = [
        (PPO, ppo_path, "./logs/",     "PPO"),
        (A2C, a2c_path, "./logs_a2c/", "A2C"),
        (DQN, dqn_path, "./logs_dqn/", "DQN"),
    ]

    all_results = {}

    for algo_cls, path, log_dir, name in configs:
        model = load_model(algo_cls, path, log_dir, use_best)
        if model is None:
            continue
        results = evaluate(model, n_episodes, name)
        all_results[name] = results

        single_out = f"evaluation_report_{name.lower()}.png"
        build_single_chart(results, name, single_out)

        wins   = sum(1 for r in results if r['winner'] == 'blue')
        losses = sum(1 for r in results if r['winner'] == 'red')
        draws  = sum(1 for r in results if r['winner'] == 'draw')
        print(f"\n{'='*55}")
        print(f"  [{name}] Итого партий : {n_episodes}")
        print(f"  [{name}] Победы       : {wins}  ({100*wins/n_episodes:.1f}%)")
        print(f"  [{name}] Поражения    : {losses}  ({100*losses/n_episodes:.1f}%)")
        print(f"  [{name}] Ничьи        : {draws}  ({100*draws/n_episodes:.1f}%)")
        print(f"  [{name}] Средняя награда : {np.mean([r['total_reward'] for r in results]):+.3f}")
        print(f"  [{name}] Средняя длина   : {np.mean([r['turns'] for r in results]):.1f} ходов")
        print("=" * 55)

    if len(all_results) >= 2:
        build_comparison_chart(all_results, out_compare)
    elif len(all_results) == 1:
        print("\nНайдена только одна модель — сравнительный отчёт не создаётся.")
    else:
        print("\nНи одной модели не найдено.")

    return all_results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Оценка PPO, A2C и DQN на RTS-среде")
    parser.add_argument("--n",    type=int,           default=None, help=f"Партий на модель (по умолч. {N_EPISODES})")
    parser.add_argument("--ppo",  type=str,           default=None, help="Путь к PPO (без .zip)")
    parser.add_argument("--a2c",  type=str,           default=None, help="Путь к A2C (без .zip)")
    parser.add_argument("--dqn",  type=str,           default=None, help="Путь к DQN (без .zip)")
    parser.add_argument("--best", action="store_true",              help="Использовать best_model из logs_*/")
    parser.add_argument("--out",  type=str,           default=None, help="Имя PNG сравнительного отчёта")
    parser.add_argument("--txt",  type=str,           default=None, help="Имя текстового отчёта (.txt)")
    args = parser.parse_args()

    run_evaluation(
        n_episodes  = args.n,
        ppo_path    = args.ppo,
        a2c_path    = args.a2c,
        dqn_path    = args.dqn,
        use_best    = args.best if args.best else None,
        out_compare = args.out,
        out_txt     = args.txt,
    )


if __name__ == "__main__":
    main()