import os
import sys
import time
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import (
    EvalCallback, CheckpointCallback
)
from stable_baselines3.common.monitor import Monitor
from rts_env import RTSEnv

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(__file__))

MODEL_PATH     = "rts_ppo_model"
LOG_DIR        = "./logs/"
N_ENVS         = 4

TOTAL_STEPS = 500_000
EVAL_FREQ = 50_000
CHECKPOINT_FREQ = 100_000

PPO_KWARGS = dict(
    learning_rate=3e-4,
    n_steps=1024,
    batch_size=128,
    n_epochs=4,
    gamma=0.995,
    gae_lambda=0.95,
    clip_range=0.2,
    ent_coef=0.03,
    vf_coef=0.5,
    max_grad_norm=0.5,
    verbose=1,
    tensorboard_log=LOG_DIR,
    policy_kwargs=dict(
        net_arch=dict(pi=[256, 256, 128], vf=[256, 256, 128])
    ),
)


def make_env():
    env = RTSEnv()
    env = Monitor(env)
    return env

def train():
    os.makedirs(LOG_DIR, exist_ok=True)
    vec_env = make_vec_env(make_env, n_envs=N_ENVS)
    eval_env = make_vec_env(make_env, n_envs=1)
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
        name_prefix="rts_ppo",
        verbose=1,
    )

    model = PPO("MlpPolicy", vec_env, **PPO_KWARGS)
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