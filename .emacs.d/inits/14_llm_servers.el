(cl-defstruct my/llm-server
  host model api-key)

(defvar my/llm-server-latest-light-chat
  (make-my/llm-server
   :host ""
   :model '()
   :api-key "TERM"))

(defvar my/llm-server-latest-chat
  (make-my/llm-server
   :host ""
   :model '()
   :api-key "TERM"))

(defvar my/llm-server-latest-light-coder
  (make-my/llm-server
   :host ""
   :model '()
   :api-key "TERM"))

(defvar my/llm-server-latest-coder
  (make-my/llm-server
   :host ""
   :model '()
   :api-key "TERM"))

(defun my/llm-server-make-endpoint (s)
  (concat "http://" (my/llm-server-host s) "/v1/chat/completions"))

(defun my/llm-server-make-base (s)
  (concat "http://" (my/llm-server-host s) "/v1/"))
