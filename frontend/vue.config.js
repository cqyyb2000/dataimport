const path = require('path') // 导入 path 模块
const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    port: 9093,
    open: false
  },
  configureWebpack: {
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src') // 默认配置
      }
    },
    watchOptions: {
      ignored: [
        '**/node_modules/**',
        '**/System Volume Information/**',
        '**/$Recycle.Bin/**'
      ],
      followSymlinks: false
    }
  }
})
