resource "aws_s3_bucket" "frontend_zona_azul" {
  bucket = "zona-azul-frontend-cloud-computing-unifei" 
}

resource "aws_s3_bucket_website_configuration" "frontend_site" {
  bucket = aws_s3_bucket.frontend_zona_azul.id

  index_document {
    suffix = "index.html"
  }
}

# Desbloqueio das travas de segurança originais da AWS (Necessário para sites públicos)
resource "aws_s3_bucket_public_access_block" "frontend_acesso" {
  bucket = aws_s3_bucket.frontend_zona_azul.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# 4. Cria a regra que permite que qualquer navegador na internet leia seus arquivos HTML/JS
resource "aws_s3_bucket_policy" "frontend_politica" {
  bucket = aws_s3_bucket.frontend_zona_azul.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend_zona_azul.arn}/*"
      },
    ]
  })
  
  # Garante que a política só seja aplicada após o desbloqueio público (Evita erros da AWS)
  depends_on = [aws_s3_bucket_public_access_block.frontend_acesso]
}

# 5. Imprime a URL pública do seu sistema no terminal no final do processo
output "url_do_site" {
  value = aws_s3_bucket_website_configuration.frontend_site.website_endpoint
}