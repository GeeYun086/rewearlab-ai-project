# Container Apps Environment
resource "azurerm_container_app_environment" "main" {
  name                       = "clothing-env"
  location                   = data.azurerm_resource_group.main.location
  resource_group_name        = data.azurerm_resource_group.main.name
  infrastructure_subnet_id   = azurerm_subnet.container_apps.id
  internal_load_balancer_enabled = false
  
  tags = {
    environment = "demo"
    project     = "clothing-resale"
  }
}

# Main App Container
resource "azurerm_container_app" "main_app" {
  name                         = "main-app"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = data.azurerm_resource_group.main.name
  revision_mode                = "Single"
  
    template {
    container {
      name   = "main-app"
      image  = "${var.acr_name}.azurecr.io/main-app:latest"
      cpu    = 2.0
      memory = "4Gi"
      
      # 기존 환경 변수들
      env {
        name  = "CHROMADB_HOST"
        value = azurerm_container_group.chromadb.ip_address
      }
      
      env {
        name  = "CHROMADB_PORT"
        value = "8000"
      }
      
      env {
        name  = "AZURE_CUSTOM_VISION_ENDPOINT"
        value = var.custom_vision_endpoint
      }
      
      env {
        name        = "AZURE_CUSTOM_VISION_KEY"
        secret_name = "custom-vision-key"
      }
      
      env {
        name  = "AZURE_CUSTOM_VISION_PROJECT_ID"
        value = var.custom_vision_project_id
      }
      
      env {
        name  = "AZURE_CUSTOM_VISION_ITERATION"
        value = var.custom_vision_iteration
      }
      
      # env {
      #   name  = "AZURE_OPENAI_ENDPOINT"
      #   value = azurerm_cognitive_account.openai.endpoint
      # }
      
      # env {
      #   name        = "AZURE_OPENAI_KEY"
      #   secret_name = "openai-key"
      # }
      
      # env {
      #   name  = "AZURE_OPENAI_DEPLOYMENT"
      #   value = azurerm_cognitive_deployment.gpt4o_mini.name
      # }
      
      # env {
      #   name  = "AZURE_OPENAI_API_VERSION"
      #   value = var.openai_api_version
      # }
    }
    
    min_replicas = 1
    max_replicas = 1
  }
  
  registry {
    server               = "${var.acr_name}.azurecr.io"
    username             = var.acr_name
    password_secret_name = "acr-password"
  }
  
  secret {
    name  = "acr-password"
    value = var.acr_password
  }
  
  secret {
    name  = "custom-vision-key"
    value = var.custom_vision_key
  }
  
  # secret {
  #   name  = "openai-key"
  #   value = azurerm_cognitive_account.openai.primary_access_key
  # }
  
  ingress {
    external_enabled = true
    target_port      = 8502
    
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
  
  tags = {
    environment = "demo"
    project     = "clothing-resale"
  }
}

# Search App Container
resource "azurerm_container_app" "search_app" {
  name                         = "search-app"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = data.azurerm_resource_group.main.name
  revision_mode                = "Single"
  
  template {
    container {
      name   = "search-app"
      image  = "${var.acr_name}.azurecr.io/search-app:latest"
      cpu    = 1.0
      memory = "2Gi"
      
      env {
        name  = "CHROMADB_HOST"
        value = azurerm_container_group.chromadb.ip_address
      }
      
      env {
        name  = "CHROMADB_PORT"
        value = "8000"
      }
    }
    
    min_replicas = 1
    max_replicas = 1
  }
  
  registry {
    server               = "${var.acr_name}.azurecr.io"
    username             = var.acr_name
    password_secret_name = "acr-password"
  }
  
  secret {
    name  = "acr-password"
    value = var.acr_password
  }
  
  ingress {
    external_enabled = true
    target_port      = 8501
    
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
  
  tags = {
    environment = "demo"
    project     = "clothing-resale"
  }
}