;; -*- lexical-binding: t; -*-

(require 'eca)

;; ECA: ストリーミング中の明示的なフォント装飾を抑制
(with-eval-after-load 'eca
  (when (boundp 'eca-chat-fontify-debounce-interval)
    (setq eca-chat-fontify-debounce-interval nil))

  ;; ストリーミング出力をまとめて反映する間隔（秒）
  (when (boundp 'eca-chat-stream-flush-interval)
    (setq eca-chat-stream-flush-interval 0.10)))

;; ECAのチャットバッファだけ、JIT Lockの装飾も遅らせる
(add-hook 'eca-chat-mode-hook
          (lambda ()
            (setq-local jit-lock-defer-time 0.5)
            (setq-local jit-lock-stealth-time nil)))
