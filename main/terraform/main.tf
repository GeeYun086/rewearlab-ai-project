# Reference existing Resource Group
data "azurerm_resource_group" "main" {
  name = var.resource_group_name
}

# Reference existing Container Registry
data "azurerm_container_registry" "acr" {
  name                = var.acr_name
  resource_group_name = data.azurerm_resource_group.main.name
}