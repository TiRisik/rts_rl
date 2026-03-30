import os
import sys
import time
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import (
    EvalCallback, CheckpointCallback
)
from stable_baselines3.common.monitor import Monitor
from rts_env import RTSEnv

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(__file__))

MODEL_PATH      = "rts_dqn_model"
LOG_DIR         = "./logs_dqn/"

TOTAL_STEPS     = 500_000
EVAL_FREQ       = 50_000
CHECKPOINT_FREQ = 100_000

DQN_KWARGS = dict(
    learning_rate=1e-4,
    buffer_size=10_000,
    learning_starts=5_000,
    batch_size=128,
    tau=1.0,
    gamma=0.995,
    train_freq=4,
    gradient_steps=1,
    target_update_interval=1_000,
    exploration_fraction=0.2,
    exploration_initial_eps=1.0,
    exploration_final_eps=0.05,
    optimize_memory_usage=False,
    verbose=1,
    tensorboard_log=LOG_DIR,
    policy_kwargs=dict(
        net_arch=[256, 256, 128]
    ),
)


def train():
    os.makedirs(LOG_DIR, exist_ok=True)
    env = Monitor(RTSEnv())
    eval_env = Monitor(RTSEnv())
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=LOG_DIR,
        log_path=LOG_DIR,
        eval_freq=EVAL_FREQ,
        n_eval_episodes=5,
        deterministic=True,
        verbose=1,
    )
    checkpoint_callback = CheckpointCallback(
        save_freq=CHECKPOINT_FREQ,
        save_path=LOG_DIR + "checkpoints/",
        name_prefix="rts_dqn",
        verbose=1,
    )

    model = DQN("MlpPolicy", env, **DQN_KWARGS)
    start = time.time()
    model.learn(
        total_timesteps=TOTAL_STEPS,
        callback=[eval_callback, checkpoint_callback],
        progress_bar=False,
    )
    elapsed = time.time() - start
    model.save(MODEL_PATH)
    return model


def main():
    model = None
    model = train()


if __name__ == "__main__":
    main()