/**
 * dsh-vibe-zhishi —— 一个纯 skill 插件。
 *
 * 它不注册任何工具，也不往页面上塞任何东西。起作用的是
 * `.dsh/skills/vibe-zhishi/SKILL.md` 那套规则：DSH 会把 skills 目录里的
 * skill 列进会话的 skill 目录，模型按需加载。
 *
 * 为什么做成「纯规则」而不是「一键出片」：
 * 渲染视频要 HyperFrames + ffmpeg，装得上也不一定跑得动；
 * 而「开头三秒为什么留不住人」这件事，不需要渲染也能判断。
 * 先把判断做对，再谈生成。
 */

export const name = 'dsh-vibe-zhishi'

/**
 * DSH 的插件入口。这里刻意留空——
 * skill 的加载走文件系统发现，不经过插件代码。
 */
export function apply() {
  // 什么都不做，是故意的。
}
