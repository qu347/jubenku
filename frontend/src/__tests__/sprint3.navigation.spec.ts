import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, shallowMount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import MaterialLibraryView from '../views/materials/MaterialLibraryView.vue'
import GenreMapView from '../views/GenreMapView.vue'
import MaterialTable from '../components/material/MaterialTable.vue'
import GenreMetricTable from '../components/genre-map/GenreMetricTable.vue'

const materialsApi=vi.hoisted(()=>({listMaterials:vi.fn(),uploadMaterials:vi.fn(),updateMaterial:vi.fn(),deleteMaterial:vi.fn(),downloadMaterial:vi.fn(),getMaterial:vi.fn()}))
const genreApi=vi.hoisted(()=>({listGenreModules:vi.fn()}))
const metricApi=vi.hoisted(()=>({listGenreMetrics:vi.fn(),createGenreMetric:vi.fn(),updateGenreMetric:vi.fn(),deleteGenreMetric:vi.fn(),getGenreMetric:vi.fn(),importGenreMetrics:vi.fn(),downloadGenreMetricTemplate:vi.fn(),exportGenreMetrics:vi.fn()}))
const confirmApi=vi.hoisted(()=>({confirmDestructive:vi.fn()}))
vi.mock('../api/materials',()=>materialsApi)
vi.mock('../api/genreModules',()=>({...genreApi,createGenreModule:vi.fn(),updateGenreModule:vi.fn(),deleteGenreModule:vi.fn(),duplicateGenreModule:vi.fn(),enableGenreModule:vi.fn(),disableGenreModule:vi.fn(),reorderGenreModules:vi.fn()}))
vi.mock('../api/genreMetrics',()=>metricApi)
vi.mock('../utils/confirm',()=>confirmApi)

const material={id:'m1',genre_module_id:'g1',genre_module:{id:'g1',name:'悬疑'},title:'线索表',material_type:'研究资料',description:'',tags:[],source:'内部',original_filename:'线索表.xlsx',stored_filename:'uuid.xlsx',storage_path:'materials/uuid.xlsx',file_extension:'xlsx',mime_type:'application/octet-stream',file_size:1024,has_attachment:true,created_at:'2026-08-11T00:00:00Z',updated_at:'2026-08-11T00:00:00Z',deleted_at:null}

describe('Sprint 3 URL 筛选状态',()=>{
  beforeEach(()=>{setActivePinia(createPinia());vi.clearAllMocks();materialsApi.listMaterials.mockResolvedValue({items:[],total:0,page:1,page_size:20,pages:0});genreApi.listGenreModules.mockResolvedValue([]);metricApi.listGenreMetrics.mockResolvedValue({items:[],total:0,page:1,page_size:100,pages:0});confirmApi.confirmDestructive.mockResolvedValue(undefined)})
  it('刷新 /materials 时从 URL 恢复筛选并发送接口参数',async()=>{const router=createRouter({history:createMemoryHistory(),routes:[{path:'/materials',component:MaterialLibraryView}]});await router.push('/materials?genre_module_id=g1&file_extension=pdf&keyword=报告');await router.isReady();shallowMount(MaterialLibraryView,{global:{plugins:[router],stubs:{'el-select':true,'el-option':true,'el-pagination':true}}});await flushPromises();expect(materialsApi.listMaterials).toHaveBeenCalledWith(expect.objectContaining({genre_module_id:'g1',file_extension:'pdf',keyword:'报告'}))})

  it('剧本库只请求 script 类型并显示独立上传入口',async()=>{const router=createRouter({history:createMemoryHistory(),routes:[{path:'/scripts',component:MaterialLibraryView,props:{libraryType:'script'}}]});await router.push('/scripts');await router.isReady();const wrapper=shallowMount(MaterialLibraryView,{props:{libraryType:'script'},global:{plugins:[router],stubs:{'el-select':true,'el-option':true,'el-pagination':true}}});await flushPromises();expect(materialsApi.listMaterials).toHaveBeenCalledWith(expect.objectContaining({library_type:'script'}));expect(wrapper.text()).toContain('剧本库');expect(wrapper.text()).toContain('上传剧本')})

  it('删除素材前执行二次确认，确认后才调用删除接口',async()=>{materialsApi.listMaterials.mockResolvedValue({items:[material],total:1,page:1,page_size:20,pages:1});materialsApi.deleteMaterial.mockResolvedValue({id:'m1'});const router=createRouter({history:createMemoryHistory(),routes:[{path:'/materials',component:MaterialLibraryView}]});await router.push('/materials');await router.isReady();const wrapper=shallowMount(MaterialLibraryView,{global:{plugins:[router],stubs:{'el-select':true,'el-option':true,'el-pagination':true}}});await flushPromises();wrapper.findComponent(MaterialTable).vm.$emit('delete',material);await flushPromises();expect(confirmApi.confirmDestructive).toHaveBeenCalledOnce();expect(materialsApi.deleteMaterial).toHaveBeenCalledWith('m1')})

  it('从 /genre-map URL 恢复平台、周期与学历筛选',async()=>{const router=createRouter({history:createMemoryHistory(),routes:[{path:'/genre-map',component:GenreMapView}]});await router.push('/genre-map?platform=番茄小说&period=2026-08&education_level=medium');await router.isReady();shallowMount(GenreMapView,{global:{plugins:[router],stubs:{'el-dropdown':true,'el-dropdown-menu':true,'el-dropdown-item':true}}});await flushPromises();expect(metricApi.listGenreMetrics).toHaveBeenCalledWith(expect.objectContaining({platform:'番茄小说',period:'2026-08',education_level:'medium'}))})

  it('定位图可切换到表格视图',async()=>{const router=createRouter({history:createMemoryHistory(),routes:[{path:'/genre-map',component:GenreMapView}]});await router.push('/genre-map');await router.isReady();const wrapper=shallowMount(GenreMapView,{global:{plugins:[router],stubs:{'el-dropdown':true,'el-dropdown-menu':true,'el-dropdown-item':true}}});await flushPromises();expect(wrapper.findComponent(GenreMetricTable).exists()).toBe(false);await wrapper.findAll('.view-switch button')[1]?.trigger('click');expect(wrapper.findComponent(GenreMetricTable).exists()).toBe(true)})
})
