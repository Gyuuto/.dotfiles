;; 警告音を消す
(setq visible-bell t)

;; 最近使ったファイル
(recentf-mode)

;; スクリプトを保存する時、自動的に chmod +x を行うようにする
(defun make-file-executable ()
  "Make the file of this buffer executable, when it is a script source."
  (save-restriction
    (widen)
    (if (string= "#!"
         (buffer-substring-no-properties 1
                         (min 3 (point-max))))
        (let ((name (buffer-file-name)))
          (or (equal ?. (string-to-char
             (file-name-nondirectory name)))
              (let ((mode (file-modes name)))
                (set-file-modes name (logior mode (logand
                           (/ mode 4) 73)))
                (message (concat "Wrote " name " (+x)"))))))))
(add-hook 'after-save-hook 'make-file-executable)

(if (equal system-type 'gnu/linux)
    ;; コピーした内容を clip-boardにもコピーします
    (setq x-select-enable-clipboard t)
)

;; setup PATH env from shell
(require 'exec-path-from-shell)
(if (string= window-system "w32")
    1
  (exec-path-from-shell-initialize)
  )

;; magit shortcut
(global-set-key (kbd "C-x g") 'magit-status)

;; dont tell uppercase from downcase
(setq completion-ignore-case t)

;; for Windows, using git-bash instead of cmd
(when (eq window-system 'w32)
  (setq explicit-shell-file-name
	"C:/Program Files/Git/bin/bash.exe")
  (setq shell-file-name explicit-shell-file-name)
  (add-to-list 'exec-path "C:/Program Files/Git/bin")
)

(add-hook 'shell-mode-hook
          (lambda ()
            ;; zsh のヒストリファイル名を設定
            (setq comint-input-ring-file-name "~/.zsh_history")
            ;; ヒストリの最大数
            (setq comint-input-ring-size 1024)
            ;; 既存の zsh ヒストリファイルを読み込み
            (comint-read-input-ring t)
            ;; zsh like completion (history-beginning-search)
            (local-set-key "\M-p" 'comint-previous-matching-input-from-input)
            (local-set-key "\M-n" 'comint-next-matching-input-from-input)
            ;; 色の設定
            (ansi-color-for-comint-mode-on)
            )
          )

; Listing directory failed but access-file worked エラーの解消
(when (eq system-type 'darwin)
  (require 'ls-lisp)
  (setq ls-lisp-use-insert-directory-program nil))
