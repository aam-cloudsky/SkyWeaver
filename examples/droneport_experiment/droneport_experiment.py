from pathlib import Path

from skyweaver.application.legacy.droneport_experiment_app import DroneportExperimentApp


def main() -> None:
    config_path = Path(
        "/Users/Davi/Documents/GitHub/SkyWeaver/examples/droneport_experiment/config.yaml"
    ).resolve()
    app = DroneportExperimentApp(config_path=str(config_path))
    app.run()


if __name__ == "__main__":
    main()
