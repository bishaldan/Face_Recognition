from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    print("Threshold calibration helper")
    print(f"Current configured threshold: {settings.default_similarity_threshold}")
    print("Recommended workflow:")
    print("1. Gather a validation set of accepted and rejected comparisons.")
    print("2. Export similarity scores from the verification pipeline.")
    print("3. Choose a threshold that balances false accepts and false rejects for your use case.")
    print("4. Update the threshold in Settings after validation.")
    print(f"Starter threshold suggestion for the current backend: {settings.default_similarity_threshold}")


if __name__ == "__main__":
    main()
