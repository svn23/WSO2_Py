import os
from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)

_FLAGS_FILE = os.path.join(os.path.dirname(__file__), "enabled_features.json")


def _banner():
    print("\n" + Fore.CYAN + "═" * 62)
    print(Fore.CYAN + Style.BRIGHT + "   🛡   SecureSphere — Learning Feature Manager")
    print(Fore.CYAN + "═" * 62)


def run():
    from features import feature_flags

    features = feature_flags.FEATURES

    # If config exists, ask to reconfigure
    if os.path.exists(_FLAGS_FILE):
        feature_flags.load()
        enabled_names = [f["name"] for f in features if feature_flags.is_enabled(f["key"])]
        _banner()
        if enabled_names:
            print(Fore.GREEN + f"\n  ✔  Active features ({len(enabled_names)}/{len(features)}):\n")
            for name in enabled_names:
                print(Fore.GREEN + f"     • {name}")
        else:
            print(Fore.YELLOW + "\n  ⚠  No optional features currently enabled (base mode).")

        print()
        try:
            answer = input(Fore.WHITE + Style.BRIGHT + "  Reconfigure? (y/n) [default: n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"

        if answer != "y":
            print(Fore.GREEN + "\n  → Keeping existing configuration. Launching...\n")
            return

    # Show selection menu
    _banner()
    print(Fore.WHITE + "\n  Select the features to enable.")
    print(Fore.YELLOW + "  Enter numbers (comma-separated), 'all', or 'none':\n")

    for i, feat in enumerate(features, 1):
        print(Fore.CYAN + Style.BRIGHT + f"  [{i:2d}]" +
              Fore.WHITE + Style.BRIGHT + f" {feat['name']}")
        print(Fore.WHITE + Style.DIM + f"        {feat['description']}\n")

    print(Fore.CYAN + "─" * 62)
    print(Fore.YELLOW + "  Examples:  '1,3,5,7'   |   'all'   |   'none'")
    print(Fore.CYAN + "─" * 62)

    selected_keys = []
    while True:
        try:
            raw = input(Fore.WHITE + Style.BRIGHT + "\n  Your selection: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            raw = "none"

        if raw == "all":
            selected_keys = [f["key"] for f in features]
            break
        elif raw in ("none", ""):
            selected_keys = []
            break
        else:
            try:
                indices = [int(x.strip()) for x in raw.split(",")]
                if all(1 <= idx <= len(features) for idx in indices):
                    selected_keys = [features[idx - 1]["key"] for idx in indices]
                    break
                else:
                    print(Fore.RED + f"  ✗ Numbers must be between 1 and {len(features)}. Try again.")
            except ValueError:
                print(Fore.RED + "  ✗ Invalid input. Use numbers, 'all', or 'none'.")

    feature_flags.save(selected_keys)

    print("\n" + Fore.CYAN + "─" * 62)
    if selected_keys:
        print(Fore.GREEN + Style.BRIGHT + f"  ✔  {len(selected_keys)} feature(s) enabled:\n")
        for key in selected_keys:
            feat = next(f for f in features if f["key"] == key)
            print(Fore.GREEN + f"     ✓ {feat['name']}")
    else:
        print(Fore.YELLOW + "  ⚠  Running in base mode — no optional features enabled.")

    print(Fore.CYAN + "─" * 62)
    print(Fore.CYAN + "\n  → Launching SecureSphere...\n")
