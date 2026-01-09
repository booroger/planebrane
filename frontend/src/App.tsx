import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Layout } from '@/components/Layout'
import { StepIndicator } from '@/components/StepIndicator'
import { UploadSection } from '@/components/UploadSection'
import { AnalysisSection } from '@/components/AnalysisSection'
import { AdjustSection } from '@/components/AdjustSection'
import { View3DSection } from '@/components/View3DSection'
import { ExportSection } from '@/components/ExportSection'
import { useAppStore } from '@/store/useAppStore'

const queryClient = new QueryClient()

function AppContent() {
  const currentStep = useAppStore((state) => state.currentStep)

  return (
    <Layout>
      <div className="flex h-full flex-col">
        <StepIndicator />
        <div className="flex-1 overflow-auto">
          {currentStep === 'upload' && <UploadSection />}
          {currentStep === 'analyze' && <AnalysisSection />}
          {currentStep === 'adjust' && <AdjustSection />}
          {currentStep === 'view3d' && <View3DSection />}
          {currentStep === 'export' && <ExportSection />}
        </div>
      </div>
    </Layout>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  )
}

export default App