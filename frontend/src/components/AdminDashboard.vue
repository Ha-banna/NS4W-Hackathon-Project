<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  Card,
  Table,
  Button,
  Input,
  Space,
  Typography,
  Modal,
  Form,
  message,
  Popconfirm
} from 'ant-design-vue'
import {
  PlusOutlined,
  DeleteOutlined,
  UserOutlined,
  MailOutlined,
  ApartmentOutlined,
  ArrowLeftOutlined
} from '@ant-design/icons-vue'
import type { ColumnsType } from 'ant-design-vue/es/table'
import { h } from 'vue'

const router = useRouter()
const { Title } = Typography

// Mock data for companies
interface Company {
  id: string
  name: string
  email: string
  employeeCount: number
}

interface Employee {
  id: string
  name: string
  email: string
  companyId: string
}

const companies = ref<Company[]>([
  { id: '1', name: 'TechCorp Inc.', email: 'contact@techcorp.com', employeeCount: 5 },
  { id: '2', name: 'InnovateLabs', email: 'hello@innovatelabs.com', employeeCount: 3 },
  { id: '3', name: 'DataSystems Ltd.', email: 'info@datasystems.com', employeeCount: 8 },
  { id: '4', name: 'CloudVentures', email: 'support@cloudventures.com', employeeCount: 2 },
])

const employees = ref<Employee[]>([
  { id: '1', name: 'John Doe', email: 'john.doe@techcorp.com', companyId: '1' },
  { id: '2', name: 'Jane Smith', email: 'jane.smith@techcorp.com', companyId: '1' },
  { id: '3', name: 'Bob Johnson', email: 'bob.johnson@techcorp.com', companyId: '1' },
  { id: '4', name: 'Alice Williams', email: 'alice.williams@techcorp.com', companyId: '1' },
  { id: '5', name: 'Charlie Brown', email: 'charlie.brown@techcorp.com', companyId: '1' },
  { id: '6', name: 'David Lee', email: 'david.lee@innovatelabs.com', companyId: '2' },
  { id: '7', name: 'Emma Davis', email: 'emma.davis@innovatelabs.com', companyId: '2' },
  { id: '8', name: 'Frank Miller', email: 'frank.miller@innovatelabs.com', companyId: '2' },
  { id: '9', name: 'Grace Wilson', email: 'grace.wilson@datasystems.com', companyId: '3' },
  { id: '10', name: 'Henry Moore', email: 'henry.moore@datasystems.com', companyId: '3' },
  { id: '11', name: 'Ivy Taylor', email: 'ivy.taylor@datasystems.com', companyId: '3' },
  { id: '12', name: 'Jack Anderson', email: 'jack.anderson@datasystems.com', companyId: '3' },
  { id: '13', name: 'Kate Martinez', email: 'kate.martinez@datasystems.com', companyId: '3' },
  { id: '14', name: 'Liam Garcia', email: 'liam.garcia@datasystems.com', companyId: '3' },
  { id: '15', name: 'Mia Rodriguez', email: 'mia.rodriguez@datasystems.com', companyId: '3' },
  { id: '16', name: 'Noah Lopez', email: 'noah.lopez@datasystems.com', companyId: '3' },
  { id: '17', name: 'Olivia Harris', email: 'olivia.harris@cloudventures.com', companyId: '4' },
  { id: '18', name: 'Paul Clark', email: 'paul.clark@cloudventures.com', companyId: '4' },
])

const selectedCompanyId = ref<string | null>(null)
const searchText = ref('')
const isCreateModalVisible = ref(false)
const createFormData = ref({
  name: '',
  email: ''
})

// Get selected company
const selectedCompany = computed(() => {
  if (!selectedCompanyId.value) return null
  return companies.value.find(c => c.id === selectedCompanyId.value)
})

// Get employees for selected company
const filteredEmployees = computed(() => {
  if (!selectedCompanyId.value) return []
  
  let filtered = employees.value.filter(e => e.companyId === selectedCompanyId.value)
  
  if (searchText.value.trim()) {
    const search = searchText.value.toLowerCase()
    filtered = filtered.filter(e => 
      e.name.toLowerCase().includes(search) || 
      e.email.toLowerCase().includes(search)
    )
  }
  
  return filtered
})

// Update employee counts
const updateEmployeeCounts = () => {
  companies.value.forEach(company => {
    company.employeeCount = employees.value.filter(e => e.companyId === company.id).length
  })
}

// Company columns
const companyColumns: ColumnsType = [
  {
    title: 'Company Name',
    dataIndex: 'name',
    key: 'name',
    width: 200,
    customRender: ({ record }: { record: Company }) => {
      return h('div', { style: 'display: flex; align-items: center; gap: 8px;' }, [
        h(ApartmentOutlined, { style: 'color: #722ed1; font-size: 18px;' }),
        h('span', { style: 'font-weight: 600;' }, record.name)
      ])
    }
  },
  {
    title: 'Email',
    dataIndex: 'email',
    key: 'email',
    width: 250,
  },
  {
    title: 'Employees',
    dataIndex: 'employeeCount',
    key: 'employeeCount',
    width: 120,
    align: 'center',
    customRender: ({ record }: { record: Company }) => {
      return h('span', { style: 'font-weight: 600; color: #b37feb;' }, record.employeeCount)
    }
  },
  {
    title: 'Action',
    key: 'action',
    width: 150,
    align: 'center',
    customRender: ({ record }: { record: Company }) => {
      return h(Button, {
        type: 'primary',
        onClick: () => handleSelectCompany(record.id)
      }, {
        default: () => 'View Employees'
      })
    }
  }
]

// Employee columns
const employeeColumns: ColumnsType = [
  {
    title: 'Name',
    dataIndex: 'name',
    key: 'name',
    width: 200,
    customRender: ({ record }: { record: Employee }) => {
      return h('div', { style: 'display: flex; align-items: center; gap: 8px;' }, [
        h(UserOutlined, { style: 'color: #722ed1;' }),
        h('span', { style: 'font-weight: 500;' }, record.name)
      ])
    }
  },
  {
    title: 'Email',
    dataIndex: 'email',
    key: 'email',
    width: 300,
    customRender: ({ record }: { record: Employee }) => {
      return h('div', { style: 'display: flex; align-items: center; gap: 8px;' }, [
        h(MailOutlined, { style: 'color: #b37feb;' }),
        h('span', record.email)
      ])
    }
  },
  {
    title: 'Action',
    key: 'action',
    width: 100,
    align: 'center',
    customRender: ({ record }: { record: Employee }) => {
      return h(Popconfirm, {
        title: 'Are you sure you want to delete this employee?',
        onConfirm: () => handleDeleteEmployee(record.id)
      }, {
        default: () => h(Button, {
          type: 'primary',
          danger: true,
          icon: h(DeleteOutlined)
        })
      })
    }
  }
]

const handleSelectCompany = (companyId: string) => {
  selectedCompanyId.value = companyId
  searchText.value = ''
}

const handleBackToCompanies = () => {
  selectedCompanyId.value = null
  searchText.value = ''
}

const handleCreateEmployee = () => {
  createFormData.value = { name: '', email: '' }
  isCreateModalVisible.value = true
}

const validateEmail = (email: string) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

const handleSubmitCreate = () => {
  if (!createFormData.value.name.trim()) {
    message.error('Please enter employee name')
    return
  }
  
  if (!createFormData.value.email.trim()) {
    message.error('Please enter employee email')
    return
  }
  
  if (!validateEmail(createFormData.value.email)) {
    message.error('Please enter a valid email address')
    return
  }
  
  // Check if email already exists for this company
  const emailExists = employees.value.some(
    e => e.email.toLowerCase() === createFormData.value.email.toLowerCase() && 
         e.companyId === selectedCompanyId.value
  )
  
  if (emailExists) {
    message.error('An employee with this email already exists in this company')
    return
  }
  
  // Create new employee
  const newEmployee: Employee = {
    id: Date.now().toString(),
    name: createFormData.value.name.trim(),
    email: createFormData.value.email.trim(),
    companyId: selectedCompanyId.value!
  }
  
  employees.value.push(newEmployee)
  updateEmployeeCounts()
  
  message.success('Employee created successfully')
  isCreateModalVisible.value = false
  createFormData.value = { name: '', email: '' }
}

const handleDeleteEmployee = (employeeId: string) => {
  const index = employees.value.findIndex(e => e.id === employeeId)
  if (index > -1) {
    employees.value.splice(index, 1)
    updateEmployeeCounts()
    message.success('Employee deleted successfully')
  }
}

// Initialize employee counts
updateEmployeeCounts()
</script>

<template>
  <div class="admin-dashboard">
    <!-- Animated Background Elements -->
    <div class="animated-bg">
      <div class="bg-circle circle-1"></div>
      <div class="bg-circle circle-2"></div>
      <div class="bg-circle circle-3"></div>
    </div>

    <div class="dashboard-container">
      <!-- Header -->
      <div class="page-header">
        <Button 
          v-if="selectedCompanyId" 
          type="text" 
          size="large" 
          class="back-button" 
          @click="handleBackToCompanies"
        >
          <template #icon>
            <ArrowLeftOutlined />
          </template>
          Back to Companies
        </Button>
        <Title :level="2" class="page-title">
          <ApartmentOutlined v-if="!selectedCompanyId" />
          <UserOutlined v-else />
          {{ selectedCompany ? selectedCompany.name + ' - Employees' : 'Admin Dashboard' }}
        </Title>
      </div>

      <!-- Companies View -->
      <Card v-if="!selectedCompanyId" class="dashboard-card">
        <div class="card-header">
          <Title :level="4" class="section-title">Companies</Title>
        </div>
        <Table
          :columns="companyColumns"
          :data-source="companies"
          :pagination="{ pageSize: 10 }"
          row-key="id"
          class="admin-table"
        />
      </Card>

      <!-- Employees View -->
      <Card v-else class="dashboard-card">
        <div class="card-header">
          <Title :level="4" class="section-title">Employees</Title>
          <Space>
            <Input
              v-model:value="searchText"
              placeholder="Search employees..."
              allow-clear
              style="width: 300px;"
              size="large"
            >
              <template #prefix>
                <UserOutlined />
              </template>
            </Input>
            <Button
              type="primary"
              size="large"
              @click="handleCreateEmployee"
            >
              <template #icon>
                <PlusOutlined />
              </template>
              Add Employee
            </Button>
          </Space>
        </div>
        <Table
          :columns="employeeColumns"
          :data-source="filteredEmployees"
          :pagination="{ pageSize: 10 }"
          row-key="id"
          class="admin-table"
        />
      </Card>
    </div>

    <!-- Create Employee Modal -->
    <Modal
      v-model:open="isCreateModalVisible"
      title="Create New Employee"
      :footer="null"
      class="create-modal"
      width="500px"
    >
      <Form layout="vertical" class="create-form">
        <Form.Item label="Full Name" required>
          <Input
            v-model:value="createFormData.name"
            placeholder="Enter employee full name"
            size="large"
          >
            <template #prefix>
              <UserOutlined />
            </template>
          </Input>
        </Form.Item>
        <Form.Item label="Email Address" required>
          <Input
            v-model:value="createFormData.email"
            type="email"
            placeholder="Enter employee email address"
            size="large"
          >
            <template #prefix>
              <MailOutlined />
            </template>
          </Input>
        </Form.Item>
        <Form.Item class="form-actions">
          <Space>
            <Button @click="isCreateModalVisible = false">Cancel</Button>
            <Button type="primary" @click="handleSubmitCreate">Create Employee</Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  </div>
</template>

<style scoped>
.admin-dashboard {
  width: 100%;
  min-height: 100vh;
  background: transparent;
  position: relative;
  padding: 40px 20px;
  font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Animated Background */
.animated-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
}

.circle-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #722ed1 0%, transparent 70%);
  animation: float1 25s ease-in-out infinite;
}

.circle-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #b37feb 0%, transparent 70%);
  animation: float2 30s ease-in-out infinite;
}

.circle-3 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, #722ed1 0%, transparent 70%);
  animation: float3 35s ease-in-out infinite;
}

@keyframes float1 {
  0% {
    transform: translate(-200px, -200px) scale(1);
  }
  25% {
    transform: translate(100px, 150px) scale(1.2);
  }
  50% {
    transform: translate(300px, -100px) scale(0.9);
  }
  75% {
    transform: translate(50px, 200px) scale(1.1);
  }
  100% {
    transform: translate(-200px, -200px) scale(1);
  }
}

@keyframes float2 {
  0% {
    transform: translate(calc(100vw + 150px), calc(50vh - 200px)) scale(1);
  }
  25% {
    transform: translate(calc(100vw - 100px), calc(50vh + 100px)) scale(1.1);
  }
  50% {
    transform: translate(calc(100vw - 400px), calc(50vh - 300px)) scale(0.8);
  }
  75% {
    transform: translate(calc(100vw - 200px), calc(50vh + 200px)) scale(1.2);
  }
  100% {
    transform: translate(calc(100vw + 150px), calc(50vh - 200px)) scale(1);
  }
}

@keyframes float3 {
  0% {
    transform: translate(calc(20vw - 300px), calc(100vh + 300px)) scale(1);
  }
  25% {
    transform: translate(calc(20vw + 200px), calc(100vh - 100px)) scale(1.3);
  }
  50% {
    transform: translate(calc(20vw + 500px), calc(100vh - 400px)) scale(0.9);
  }
  75% {
    transform: translate(calc(20vw + 100px), calc(100vh - 200px)) scale(1.1);
  }
  100% {
    transform: translate(calc(20vw - 300px), calc(100vh + 300px)) scale(1);
  }
}

.dashboard-container {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.page-header {
  margin-bottom: 32px;
  text-align: center;
}

.back-button {
  color: rgba(255, 255, 255, 0.7);
  padding: 8px 16px;
  height: auto;
  margin-bottom: 24px;
}

.back-button:hover {
  color: #b37feb;
  background: rgba(114, 46, 209, 0.1);
}

.page-title {
  margin-bottom: 0 !important;
  background: linear-gradient(135deg, #722ed1 0%, #b37feb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 2.5rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.dashboard-card {
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(114, 46, 209, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.dashboard-card :deep(.ant-card-body) {
  padding: 32px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.section-title {
  margin: 0 !important;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  font-size: 1.5rem;
}

.admin-table {
  background: transparent;
}

.admin-table :deep(.ant-table) {
  background: transparent;
}

.admin-table :deep(.ant-table-thead > tr > th) {
  background: rgba(114, 46, 209, 0.1);
  border-bottom: 1px solid rgba(114, 46, 209, 0.3);
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
}

.admin-table :deep(.ant-table-tbody > tr > td) {
  border-bottom: 1px solid rgba(114, 46, 209, 0.1);
  color: rgba(255, 255, 255, 0.8);
}

.admin-table :deep(.ant-table-tbody > tr:hover > td) {
  background: rgba(114, 46, 209, 0.05);
}

.admin-table :deep(.ant-table-tbody > tr) {
  background: transparent;
}

.admin-table :deep(.ant-pagination) {
  margin-top: 24px;
}

.admin-table :deep(.ant-pagination-item) {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(114, 46, 209, 0.3);
}

.admin-table :deep(.ant-pagination-item a) {
  color: rgba(255, 255, 255, 0.8);
}

.admin-table :deep(.ant-pagination-item-active) {
  background: #722ed1;
  border-color: #722ed1;
}

.admin-table :deep(.ant-pagination-item-active a) {
  color: #fff;
}

.admin-table :deep(.ant-pagination-prev),
.admin-table :deep(.ant-pagination-next) {
  color: rgba(255, 255, 255, 0.8);
}

.admin-table :deep(.ant-input) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(114, 46, 209, 0.3);
  color: rgba(255, 255, 255, 0.9);
}

.admin-table :deep(.ant-input):focus {
  border-color: #722ed1;
  box-shadow: 0 0 0 2px rgba(114, 46, 209, 0.2);
}

.admin-table :deep(.ant-input)::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.admin-table :deep(.ant-input-prefix) {
  color: rgba(255, 255, 255, 0.6);
}

/* Modal Styles */
.create-modal :deep(.ant-modal-content) {
  background: rgba(26, 26, 46, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(114, 46, 209, 0.3);
}

.create-modal :deep(.ant-modal-header) {
  background: transparent;
  border-bottom: 1px solid rgba(114, 46, 209, 0.2);
}

.create-modal :deep(.ant-modal-title) {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
}

.create-modal :deep(.ant-modal-close) {
  color: rgba(255, 255, 255, 0.7);
}

.create-modal :deep(.ant-modal-close:hover) {
  color: #b37feb;
}

.create-form :deep(.ant-form-item-label > label) {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
}

.create-form :deep(.ant-input) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(114, 46, 209, 0.3);
  color: rgba(255, 255, 255, 0.9);
}

.create-form :deep(.ant-input):focus {
  border-color: #722ed1;
  box-shadow: 0 0 0 2px rgba(114, 46, 209, 0.2);
}

.create-form :deep(.ant-input)::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.create-form :deep(.ant-input-prefix) {
  color: rgba(255, 255, 255, 0.6);
}

.form-actions {
  margin-top: 24px;
  margin-bottom: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .page-title {
    font-size: 2rem;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .dashboard-card :deep(.ant-card-body) {
    padding: 20px;
  }
}
</style>
