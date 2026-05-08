
import subprocess
import os
import sys

def run_command(command, cwd=None, check_railway_cli=False):
    """Executa um comando shell e imprime sua saída."""
    shell_exec = sys.platform.startswith("win")

    try:
        result = subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True, encoding='utf-8', shell=shell_exec)
        print(result.stdout)
        return result.stdout
    except FileNotFoundError:
        if check_railway_cli:
            print("Erro: O comando 'railway' não foi encontrado.")
            sys.exit(1)
        else:
            print(f"Erro: Comando não encontrado: {command[0]}")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        # Silenciar erros de status se estivermos apenas tentando linkar
        if "status" in command:
            return None
        print(f"Erro ao executar comando: {e}")
        print(f"Stderr: {e.stderr}")
        return None

def deploy_bot_to_railway(bot_path, project_id=None, environment=None):
    """Automatiza o deploy do bot para o Railway."""
    print(f"Iniciando deploy do bot em: {bot_path}")
    
    # Verificar CLI
    run_command(["railway", "--version"], check_railway_cli=True)

    # Comando de deploy base
    deploy_command = ["railway", "up"]
    
    if project_id:
        print(f"Forçando deploy para o projeto: {project_id}")
        deploy_command.extend(["--project", project_id])
    
    if environment:
        deploy_command.extend(["--environment", environment])
    else:
        # Se usar --project, o --environment é obrigatório no Railway CLI
        deploy_command.extend(["--environment", "production"])
    
    print(f"Executando: {' '.join(deploy_command)}")
    print("Isso pode levar alguns minutos dependendo do tamanho do bot...")
    
    run_command(deploy_command, cwd=bot_path)
    print("\nProcesso de deploy finalizado! Verifique o painel do Railway para acompanhar o build.")

if __name__ == "__main__":
    bot_directory = os.path.abspath(os.path.dirname(__file__))
    
    arg_project_id = sys.argv[1] if len(sys.argv) > 1 else None
    arg_environment = sys.argv[2] if len(sys.argv) > 2 else "production"

    deploy_bot_to_railway(bot_directory, arg_project_id, arg_environment)
