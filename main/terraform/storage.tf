# Storage Account for ChromaDB data
resource "azurerm_storage_account" "chromadb" {
  name                     = "chromadbstorage${random_string.suffix.result}"
  resource_group_name      = data.azurerm_resource_group.main.name
  location                 = data.azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  
  tags = {
    environment = "demo"
    project     = "clothing-resale"
  }
}

# File Share for ChromaDB persistent data
resource "azurerm_storage_share" "chromadb" {
  name                 = "chromadb-data"
  storage_account_name = azurerm_storage_account.chromadb.name
  quota                = 5  # 5GB quota
}

# Random suffix for unique names
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}