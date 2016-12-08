;; setup anything
(require 'anything-startup)
(global-set-key (kbd "C-x :") 'anything)

(when (eq system-type 'darwin)
  (setq ns-command-modifier (quote meta)))

(defun my-choose-completion ()
  "Choose the completion that point is in or next to."
  (interactive)
  (let (beg end completion (buffer completion-reference-buffer)
	(base-size completion-base-size))
    (if (and (not (eobp)) (get-text-property (point) 'mouse-face))
	(setq end (point) beg (1+ (point))))
    (if (and (not (bobp)) (get-text-property (1- (point)) 'mouse-face))
	(setq end (1- (point)) beg (point)))
    (if (null beg)
	(error "No completion here"))
    (setq beg (previous-single-property-change beg 'mouse-face))
    (setq end (or (next-single-property-change end 'mouse-face) (point-max)))
    (setq completion (buffer-substring-no-properties beg end))
    (delete-completion-window)
    (choose-completion-string completion buffer base-size))
)
