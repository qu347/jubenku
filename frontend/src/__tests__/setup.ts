import { config } from '@vue/test-utils'

config.global.stubs = {
  'el-icon': { template: '<span><slot /></span>' },
  'el-button': { template: '<button><slot /></button>' },
}

config.global.directives = {
  loading: { mounted() {} },
}
