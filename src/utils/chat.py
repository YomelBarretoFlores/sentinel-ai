import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.knowledge import kb


def chat_loop():
    print("Sentinel AI - Consulta de Base de Conocimiento")
    print("=" * 48)
    print("Escribe 'salir' para terminar la sesion.")
    print("=" * 48)

    if not kb:
        print("[ERROR] La base de conocimiento no esta inicializada. Verifica las credenciales.")
        return

    while True:
        try:
            user_input = input("\nConsulta: ")
            if user_input.lower() in ["salir", "exit", "quit"]:
                print("Sesion finalizada.")
                break

            print("Procesando consulta...", end="\r")
            response = kb.query(user_input)
            print(" " * 30, end="\r")
            print(f"Sentinel AI: {response}")

        except KeyboardInterrupt:
            print("\nSesion finalizada.")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")


if __name__ == "__main__":
    chat_loop()
