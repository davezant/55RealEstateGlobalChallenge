class ValidationFailed(Exception):
    def __init__(self, fields: list[tuple[str, str]], status_code: int = 422):
        super().__init__("validacao")
        self.fields = fields
        self.status_code = status_code

class NotFound(Exception):
    pass

class UploadRejected(Exception):
    def __init__(self, code: str, status_code: int):
        super().__init__(code)
        self.code = code
        self.status_code = status_code

MESSAGES = {
    "obrigatorio": "Campo obrigatório.",
    "invalido": "Valor inválido.",
    "muito_curto": "Texto curto demais.",
    "muito_longo": "Texto longo demais.",
    "deve_ser_positivo": "Informe um valor maior que zero.",
    "nao_negativo": "Informe um valor igual ou maior que zero.",
    "formato_invalido": "Formato inválido.",
    "casas_decimais": "Use no máximo 2 casas decimais.",
    "digitos_demais": "Número grande demais.",
    "nao_se_aplica": "Não se aplica a esta tipologia.",
    "moeda_incompativel": "A moeda não corresponde à praça.",
    "ref_duplicada": "Esta referência já está cadastrada.",
    "slug_duplicado": "Este endereço já está em uso.",
    "foto_obrigatoria": "Publique com pelo menos uma foto.",
    "descricao_foto_obrigatoria": "Toda foto precisa de descrição.",
    "transicao_invalida": "Esta mudança de situação não é permitida.",
    "vendido_irreversivel": "Imóvel vendido não volta a ser oferecido.",
    "situacao_invalida": "Situação inválida.",
    "limite_fotos": "O limite é de 12 fotos por imóvel.",
    "arquivo_ausente": "Envie um arquivo.",
    "arquivo_grande": "A foto passa de 5 MB.",
    "tipo_invalido": "Use JPEG, PNG ou WebP.",
}

def message_for(code: str) -> str:
    return MESSAGES.get(code, "Valor inválido.")
