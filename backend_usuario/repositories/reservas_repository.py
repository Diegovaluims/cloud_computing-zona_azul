from datetime import datetime

class ReservaRepository:
    def __init__(self, cursor):
        """
        Inicializa o repositório com o cursor do banco de dados,
        permitindo a injeção de dependência via a rota.
        """
        self.cursor = cursor

    def veiculo_pertence_ao_usuario(self, id_usuario: int, placa: str) -> bool:
        """
        Verifica se a placa fornecida está vinculada ao usuário na tabela de relacionamento.
        """
        # Verificação de Vínculo de Veículo
        query = "SELECT 1 FROM usuario_veiculo WHERE id_usuario = %s AND placa = %s;"
        self.cursor.execute(query, (id_usuario, placa))
        return self.cursor.fetchone() is not None

    def buscar_id_veiculo_por_placa(self, placa: str) -> int:
        """
        Retorna o ID interno do veículo com base na placa.
        """
        # Busca do ID do Veículo
        self.cursor.execute("SELECT id_veiculo FROM veiculos WHERE placa = %s;", (placa,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def buscar_saldo_usuario_for_update(self, id_usuario: int) -> float:
        """
        Busca o saldo atual do usuário e aplica um 'lock' na linha 
        (FOR UPDATE) para evitar concorrência durante a dedução.
        """
        # Busca de Saldo com Lock
        self.cursor.execute("SELECT saldo FROM usuarios WHERE id_usuario = %s FOR UPDATE;", (id_usuario,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def verificar_conflito_horario_for_update(self, id_veiculo: int, hora_inicio: datetime, hora_fim: datetime) -> bool:
        """
        Verifica se o veículo já possui uma reserva ativa no período desejado.
        Aplica um lock nas reservas para evitar conflitos concorrentes.
        """
        # Verificação de Conflitos de Horário com Lock
        query = """
            SELECT 1 FROM reservas 
            WHERE id_veiculo = %s AND status = 'ATIVA'
              AND (hora_fim > %s AND hora_inicio < %s)
            FOR UPDATE;
        """
        self.cursor.execute(query, (id_veiculo, hora_inicio, hora_fim))
        return self.cursor.fetchone() is not None

    def deduzir_saldo(self, id_usuario: int, valor: float):
        """
        Subtrai o valor da reserva do saldo atual do usuário.
        """
        # Dedução do Saldo do Usuário
        query = "UPDATE usuarios SET saldo = saldo - %s WHERE id_usuario = %s;"
        self.cursor.execute(query, (valor, id_usuario))

    def inserir_reserva(self, id_usuario: int, id_veiculo: int, id_setor: int, hora_inicio: datetime, hora_fim: datetime, valor_pago: float) -> int:
        """
        Insere a nova reserva na tabela e retorna o ID da reserva criada.
        """
        # Inserção da Reserva
        query = """
            INSERT INTO reservas (id_usuario, id_veiculo, id_setor, hora_inicio, hora_fim, valor_pago, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'ATIVA')
            RETURNING id_reserva;
        """
        self.cursor.execute(query, (id_usuario, id_veiculo, id_setor, hora_inicio, hora_fim, valor_pago))
        return self.cursor.fetchone()[0]
