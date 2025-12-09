# ChromaDB Container Instance
resource "azurerm_container_group" "chromadb" {
  name                = "chromadb-instance"
  location            = data.azurerm_resource_group.main.location
  resource_group_name = data.azurerm_resource_group.main.name
  ip_address_type     = "Private"
  subnet_ids          = [azurerm_subnet.container_instances.id]  
  os_type             = "Linux"
  
  container {
    name   = "chromadb"
    image  = "smuteam1clothingresale.azurecr.io/chromadb:latest"
    cpu    = "2"
    memory = "4"
    
    ports {
      port     = 8000
      protocol = "TCP"
    }
    
    volume {
      name                 = "chromadb-data"
      mount_path           = "/data"
      storage_account_name = azurerm_storage_account.chromadb.name
      storage_account_key  = azurerm_storage_account.chromadb.primary_access_key
      share_name           = azurerm_storage_share.chromadb.name
    }
  }
  
  tags = {
    environment = "demo"
    project     = "clothing-resale"
  }

  # ACR 인증
  image_registry_credential {
    server   = data.azurerm_container_registry.acr.login_server
    username = data.azurerm_container_registry.acr.admin_username
    password = data.azurerm_container_registry.acr.admin_password
  }
}