# Docker aliases and functions

export alias doc = docker
export alias docc = docker compose

export def docker_prune [] {
  docker system prune --volumes -fa
}
