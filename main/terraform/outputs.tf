output "main_app_url" {
  description = "Main App URL"
  value       = "https://${azurerm_container_app.main_app.ingress[0].fqdn}"
}

output "search_app_url" {
  description = "Search App URL"
  value       = "https://${azurerm_container_app.search_app.ingress[0].fqdn}"
}

output "chromadb_ip" {
  description = "ChromaDB Private IP Address"
  value       = azurerm_container_group.chromadb.ip_address
}

output "storage_account_name" {
  description = "Storage Account Name for ChromaDB data"
  value       = azurerm_storage_account.chromadb.name
}

output "file_share_name" {
  description = "File Share Name for ChromaDB data"
  value       = azurerm_storage_share.chromadb.name
}

# output "openai_endpoint" {
#   description = "Azure OpenAI Endpoint"
#   value       = azurerm_cognitive_account.openai.endpoint
# }

# output "openai_deployment_name" {
#   description = "Azure OpenAI Deployment Name"
#   value       = azurerm_cognitive_deployment.gpt4o_mini.name
# }