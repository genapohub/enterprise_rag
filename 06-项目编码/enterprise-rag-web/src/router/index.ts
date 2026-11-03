import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('@/layouts/AppLayout.vue'),
      children: [
        { path: '', redirect: '/knowledge-bases' },
        {
          path: 'knowledge-bases',
          name: 'knowledge-bases',
          component: () => import('@/views/KnowledgeBasesView.vue'),
          meta: { title: '知识库' },
        },
        {
          path: 'knowledge-bases/:id/docs',
          name: 'kb-docs',
          component: () => import('@/views/DocumentsView.vue'),
          meta: { title: '文档管理' },
        },
        {
          path: 'chat',
          name: 'chat',
          component: () => import('@/views/ChatView.vue'),
          meta: { title: '对话问答' },
        },
        {
          path: 'members',
          name: 'members',
          component: () => import('@/views/MembersView.vue'),
          meta: { title: '成员与角色', adminOnly: true },
        },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/knowledge-bases' },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && auth.isAuthenticated) {
    return { name: 'knowledge-bases' }
  }
  if (to.meta.adminOnly && !auth.isAdmin) {
    return { name: 'knowledge-bases' }
  }
  return true
})

export default router
