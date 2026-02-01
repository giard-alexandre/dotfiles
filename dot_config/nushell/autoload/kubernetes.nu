# Kubernetes aliases and functions

export alias kubectx = kubectl ctx
export alias kubens = kubectl ns
export alias kx = kubectx
export alias kn = kubens
export alias k = kubectl
export alias sk = kubectl -n kube-system
export alias ke = EDITOR=vim kubectl edit
export alias klbaddr = kubectl get svc -ojsonpath='{.status.loadBalancer.ingress[0].hostname}'
export alias kdebug = kubectl run -i -t debug --rm --image=caarlos0/debug --restart=Never
export alias knrunning = kubectl get pods --field-selector=status.phase!=Running
export alias kfails = kubectl get po -owide --all-namespaces | grep "0/" | tee /dev/tty | wc -l
export alias kimg = kubectl get deployment --output=jsonpath='{.spec.template.spec.containers[*].image}'
export alias kvs = kubectl view-secret

# Base64 encode/decode for Kubernetes secrets
export def kenc [...args: string] {
  $args | str join " " | encode base64
}

export def kdec [encoded: string] {
  $encoded | decode base64
}

# Create k3d test cluster
export def ktc [] {
  k3d create --name test --wait 0
  let kubeconfig = (^k3d get-kubeconfig --name='test' | str trim)
  $env.KUBECONFIG = $kubeconfig
}
