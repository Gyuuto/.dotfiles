(use-package ellama
  :ensure t
  :bind ("C-c g" . ellama-transient-main-menu)
  :init
  (setopt ellama-language "Japanese")
  (require 'llm-ollama)

  ;; set provider
  (setopt ellama-provider
          (make-llm-ollama
           :host ""
           :port 11434
           :chat-model "gemma3:4b"
           :embedding-model "gemma3:4b"
           )
          )
  ;; (setopt ellama-summarization-provider
  ;;         )
  ;; (setopt ellama-coding-provider
  ;;         )
  ;; (setopt ellama-naming-provider
  ;;         )
  ;; (setopt ellama-translation-provider
  ;;         )

  ;; customize display
  (push '("ellama.*\.org" :regexp t :height 0.5) popwin:special-display-config)
  )
