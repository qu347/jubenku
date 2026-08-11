import { ElMessageBox } from 'element-plus'

export async function confirmDestructive(message: string, title: string): Promise<void> {
  await ElMessageBox.confirm(message, title, {
    type: 'warning',
    confirmButtonText: '确认删除',
    cancelButtonText: '取消',
  })
}
