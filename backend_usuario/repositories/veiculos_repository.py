# Padrão de Projeto: Repository
# Aqui concentramos toda a lógica que fala DIRETAMENTE com o banco de dados.
# Se um dia migrarmos do PostgreSQL para o MySQL, mudaremos apenas os arquivos 
# dentro desta pasta, sem mexer nas rotas do FastAPI!

class VeiculoRepository:
    def __init__(self, cursor):
        """
        Inicializa o repositório com o cursor do banco de dados,
        permitindo injeção de dependência na rota.
        """
        self.cursor = cursor

    def inserir_veiculo_e_vincular(self, id_usuario: int, placa: str, modelo: str, ano: int):
        """
        Insere um novo veículo (se não existir) e cria o vínculo com o usuário.
        """
        # Cadastro do Veículo
        # ON CONFLICT garante que se a placa já existir, não dará erro (idempotência).
        query_carro = """
            INSERT INTO veiculos (placa, modelo, ano) 
            VALUES (%s, %s, %s) ON CONFLICT (placa) DO NOTHING;
        """
        self.cursor.execute(query_carro, (placa, modelo, ano))
        
        # Vínculo do Veículo com o Usuário
        query_vinculo = """
            INSERT INTO usuario_veiculo (id_usuario, placa) 
            VALUES (%s, %s);
        """
        self.cursor.execute(query_vinculo, (id_usuario, placa))

    def listar_por_usuario(self, id_usuario: int):
        """
        Busca todos os veículos associados a um usuário específico.
        """
        # Busca de Veículos Vinculados
        query = """
            SELECT v.placa, v.modelo, v.ano 
            FROM veiculos v
            JOIN usuario_veiculo uv ON v.placa = uv.placa
            WHERE uv.id_usuario = %s;
        """
        self.cursor.execute(query, (id_usuario,))
        return self.cursor.fetchall()
