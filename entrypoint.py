from config.settings import loaded_config

if loaded_config.mode == "server":
    from app.main import main as server_main

    if __name__ == "__main__":
        server_main()
else:
    print('MODE not available')
