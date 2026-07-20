import os
import subprocess
import sys
import platform

VENV_NAME = ".venv"
REQ_FILE = os.path.join(".requirements", "requirements.txt")

def run_command(command):
    print(f">> {command}")
    subprocess.run(command, shell=True, check=True)

def nuke_dir(dir_path):
    print(f"Suppression forcée de '{dir_path}'...")
    # Utilisation des commandes natives de l'OS pour éviter les bugs de symlinks inter-systèmes
    if platform.system() == "Windows":
        subprocess.run(f'rmdir /s /q "{dir_path}"', shell=True)
    else:
        subprocess.run(f'rm -rf "{dir_path}"', shell=True)

def main():
    if platform.system() == "Windows":
        venv_python = os.path.join(VENV_NAME, "Scripts", "python.exe")
    else:
        venv_python = os.path.join(VENV_NAME, "bin", "python")

    # Vérification de l'intégrité de l'environnement
    if os.path.exists(VENV_NAME):
        if not os.path.exists(venv_python):
            print(f"Environnement invalide détecté pour {platform.system()}. Nettoyage en cours...")
            nuke_dir(VENV_NAME)
        else:
            print(f"'{VENV_NAME}' existe déjà et est valide.")

    # Création
    if not os.path.exists(VENV_NAME):
        print(f"Création de '{VENV_NAME}'...")
        run_command(f'"{sys.executable}" -m venv {VENV_NAME}')

    # Mise à jour et installation
    print("Updating pip...")
    run_command(f'"{venv_python}" -m pip install --upgrade pip')

    print("Installing required dependencies...")
    if os.path.exists(REQ_FILE):
        run_command(f'"{venv_python}" -m pip install -r "{REQ_FILE}"')
    else:
        print(f"Erreur : le fichier {REQ_FILE} est introuvable.")

    print(f"\n'{VENV_NAME}' operational.")
    print("Pour activer ton environnement manuellement, tape :")
    
    if platform.system() == "Windows":
        print(f"-> {VENV_NAME}\\Scripts\\activate")
    else:
        print(f"-> source {VENV_NAME}/bin/activate")

if __name__ == "__main__":
    main()