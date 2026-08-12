import { ElMessageBox } from 'element-plus'

/** Show generated password once; user must acknowledge before closing. */
export async function showPasswordOnce(
  password: string,
  title = '密码已生成',
): Promise<void> {
  await ElMessageBox.alert(
    `请妥善保存以下密码，关闭后将无法再次查看：\n\n${password}\n\n建议复制后粘贴到安全位置。`,
    title,
    {
      confirmButtonText: '我已保存',
      type: 'warning',
      dangerouslyUseHTMLString: false,
    },
  )
}
