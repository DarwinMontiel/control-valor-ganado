import type { ReactNode } from 'react'

import { Modal } from './Modal'
import { Button } from './ui'

interface ConfirmDialogProps {
  open: boolean
  title: string
  confirmLabel: string
  pending: boolean
  onConfirm: () => void
  onCancel: () => void
  children: ReactNode
}

export function ConfirmDialog({
  open,
  title,
  confirmLabel,
  pending,
  onConfirm,
  onCancel,
  children,
}: ConfirmDialogProps) {
  return (
    <Modal open={open} title={title} onClose={onCancel}>
      <div className="text-sm text-muted">{children}</div>
      <div className="mt-6 flex justify-end gap-2">
        <Button variant="secondary" onClick={onCancel} disabled={pending}>
          Cancelar
        </Button>
        <Button variant="danger" onClick={onConfirm} disabled={pending}>
          {pending ? 'Eliminando…' : confirmLabel}
        </Button>
      </div>
    </Modal>
  )
}
