group "default" {
	targets = ["debian-latest", "debian-19", "debian-18", "debian-17", "debian-16", "debian-11"]
}

variable "REGISTRY_PREFIX" {
	default = ""
}

variable "IMAGE_NAME" {
	default = "cmdbsyncer"
}

variable "BUILD_REVISION" {
	default = ""
}

target "debian" {
	args = {"GOCRONVER" = "v0.0.10"}
	dockerfile = "Dockerfile"
}


target "debian-latest" {
	inherits = ["debian"]
	platforms = ["linux/amd64", "linux/arm64"]
	args = {"BASETAG" = "20"}
	tags = [
		"${REGISTRY_PREFIX}${IMAGE_NAME}:latest",
		"${REGISTRY_PREFIX}${IMAGE_NAME}:20",
		notequal("", BUILD_REVISION) ? "${REGISTRY_PREFIX}${IMAGE_NAME}:20-debian-${BUILD_REVISION}" : ""
	]
}

target "debian-19" {
	inherits = ["debian"]
	platforms = ["linux/amd64", "linux/arm64"]
	args = {"BASETAG" = "19"}
	tags = [
		"${REGISTRY_PREFIX}${IMAGE_NAME}:19",
		notequal("", BUILD_REVISION) ? "${REGISTRY_PREFIX}${IMAGE_NAME}:19-debian-${BUILD_REVISION}" : ""
	]
}

target "debian-18" {
	inherits = ["debian"]
	platforms = ["linux/amd64", "linux/arm64"]
	args = {"BASETAG" = "18"}
	tags = [
		"${REGISTRY_PREFIX}${IMAGE_NAME}:18",
		notequal("", BUILD_REVISION) ? "${REGISTRY_PREFIX}${IMAGE_NAME}:18-debian-${BUILD_REVISION}" : ""
	]
}


target "debian-17" {
	inherits = ["debian"]
	platforms = ["linux/amd64", "linux/arm64"]
	args = {"BASETAG" = "17"}
	tags = [
		"${REGISTRY_PREFIX}${IMAGE_NAME}:17",
		notequal("", BUILD_REVISION) ? "${REGISTRY_PREFIX}${IMAGE_NAME}:17-debian-${BUILD_REVISION}" : ""
	]
}

target "debian-16" {
	inherits = ["debian"]
	platforms = ["linux/amd64", "linux/arm64"]
	args = {"BASETAG" = "16"}
	tags = [
		"${REGISTRY_PREFIX}${IMAGE_NAME}:16",
		notequal("", BUILD_REVISION) ? "${REGISTRY_PREFIX}${IMAGE_NAME}:16-debian-${BUILD_REVISION}" : ""
	]
}

target "debian-11" {
	inherits = ["debian"]
	platforms = ["linux/amd64", "linux/arm64"]
	args = {"BASETAG" = "11"}
	tags = [
		"${REGISTRY_PREFIX}${IMAGE_NAME}:11",
		notequal("", BUILD_REVISION) ? "${REGISTRY_PREFIX}${IMAGE_NAME}:11-debian-${BUILD_REVISION}" : ""
	]
}

