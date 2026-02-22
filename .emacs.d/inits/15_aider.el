(use-package aidermacs
  :ensure t
  :bind (("C-c C-a" . aidermacs-transient-menu))
  :config
  (setenv "OLLAMA_API_BASE" "")
  ;; (setenv "OPENAI_API_BASE" "")
  :custom
  (aidermacs-default-chat-model "ollama_chat/")
  (aidermacs-default-model "ollama_chat/")
  ;; (aidermacs-default-chat-model "openai/")
  ;; (aidermacs-default-model "openai/")
  )
