variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "smu-team1"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "koreacentral"
}

variable "acr_name" {
  description = "Azure Container Registry name"
  type        = string
  default     = "smuteam1clothingresale"
}

variable "acr_password" {
  description = "Azure Container Registry admin password"
  type        = string
  sensitive   = true
}

variable "custom_vision_endpoint" {
  description = "Azure Custom Vision Prediction Endpoint"
  type        = string
  sensitive   = true
}

variable "custom_vision_key" {
  description = "Azure Custom Vision Prediction Key"
  type        = string
  sensitive   = true
}

variable "custom_vision_project_id" {
  description = "Azure Custom Vision Project ID"
  type        = string
  sensitive   = true
}

variable "custom_vision_iteration" {
  description = "Azure Custom Vision Iteration name"
  type        = string
  default     = "Iteration1"
}

# variable "openai_endpoint" {
#   description = "Azure OpenAI Endpoint"
#   type        = string
#   sensitive   = true
# }

# variable "openai_key" {
#   description = "Azure OpenAI API Key"
#   type        = string
#   sensitive   = true
# }

variable "openai_api_version" {
  description = "Azure OpenAI API Version"
  type        = string
  default     = "2024-02-15-preview"
}

variable "openai_deployment" {
  description = "Azure OpenAI Deployment Name"
  type        = string
  default     = "gpt-4o-mini"
}