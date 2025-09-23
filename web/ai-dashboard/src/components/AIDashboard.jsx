import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Switch,
  FormControlLabel,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Tab,
  Tabs,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Psychology,
  Speed,
  Memory,
  Timeline,
  Settings,
  Assessment,
  DataObject,
  SmartToy,
  ExpandMore,
  Refresh,
  TrendingUp,
  Warning,
  CheckCircle,
  Error
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar
} from 'recharts';

const AIDashboard = () => {
  const [aiStatus, setAiStatus] = useState(null);
  const [performanceMetrics, setPerformanceMetrics] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [knowledgeStats, setKnowledgeStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(0);
  const [optimizationEnabled, setOptimizationEnabled] = useState(true);
  const [configDialog, setConfigDialog] = useState(false);

  // Симуляция данных (в реальной системе - API вызовы)
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      
      // Симуляция загрузки данных
      setTimeout(() => {
        setAiStatus({
          is_running: true,
          uptime_seconds: 3600,
          stats: {
            decisions_made: 45,
            predictions_generated: 128,
            knowledge_entries_added: 23
          },
          optimization_enabled: true,
          components: {
            ai_engine: 'active',
            algorithms: 'active',
            knowledge_base: 'active',
            optimizer: 'active'
          }
        });

        setPerformanceMetrics([
          { time: '10:00', cpu: 25, memory: 45, decisions: 5 },
          { time: '10:05', cpu: 30, memory: 48, decisions: 8 },
          { time: '10:10', cpu: 28, memory: 52, decisions: 6 },
          { time: '10:15', cpu: 35, memory: 55, decisions: 12 },
          { time: '10:20', cpu: 32, memory: 51, decisions: 9 },
          { time: '10:25', cpu: 29, memory: 49, decisions: 7 }
        ]);

        setDecisions([
          {
            id: 1,
            action: 'optimize_memory_usage',
            confidence: 0.87,
            timestamp: '2025-01-20 10:25:30',
            status: 'executed',
            outcome: 'successful'
          },
          {
            id: 2,
            action: 'restart_failed_services',
            confidence: 0.95,
            timestamp: '2025-01-20 10:20:15',
            status: 'executed',
            outcome: 'successful'
          },
          {
            id: 3,
            action: 'analyze_market_trends',
            confidence: 0.73,
            timestamp: '2025-01-20 10:15:45',
            status: 'in_progress',
            outcome: 'pending'
          }
        ]);

        setKnowledgeStats({
          total_entries: 1247,
          categories: {
            'AI/ML': 324,
            'Trading': 289,
            'System': 198,
            'Analytics': 156,
            'Security': 98,
            'Other': 182
          },
          recent_growth: 15,
          cache_hit_rate: 0.78
        });

        setLoading(false);
      }, 1000);
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Обновление каждые 30 секунд

    return () => clearInterval(interval);
  }, []);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
      case 'executed':
      case 'successful':
        return 'success';
      case 'warning':
      case 'in_progress':
      case 'pending':
        return 'warning';
      case 'error':
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatUptime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}ч ${minutes}м`;
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Загрузка ИИ-дашборда...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3, backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
      {/* Заголовок */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
          <Psychology sx={{ mr: 1, verticalAlign: 'bottom' }} />
          Mirai AI Dashboard
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={() => window.location.reload()}
            sx={{ mr: 2 }}
          >
            Обновить
          </Button>
          <Button
            variant="contained"
            startIcon={<Settings />}
            onClick={() => setConfigDialog(true)}
          >
            Настройки
          </Button>
        </Box>
      </Box>

      {/* Статус системы */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <SmartToy color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Статус ИИ</Typography>
              </Box>
              <Chip
                icon={<CheckCircle />}
                label={aiStatus?.is_running ? 'Активен' : 'Неактивен'}
                color={aiStatus?.is_running ? 'success' : 'error'}
                sx={{ mb: 1 }}
              />
              <Typography variant="body2" color="textSecondary">
                Время работы: {formatUptime(aiStatus?.uptime_seconds || 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <Assessment color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Решения</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {aiStatus?.stats?.decisions_made || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Принято решений
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <Timeline color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Прогнозы</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {aiStatus?.stats?.predictions_generated || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Создано прогнозов
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <DataObject color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Знания</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {aiStatus?.stats?.knowledge_entries_added || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Новых записей
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Вкладки */}
      <Card>
        <Tabs value={activeTab} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label="Производительность" icon={<Speed />} />
          <Tab label="Решения" icon={<Psychology />} />
          <Tab label="База знаний" icon={<DataObject />} />
          <Tab label="Компоненты" icon={<Settings />} />
        </Tabs>

        {/* Вкладка производительности */}
        {activeTab === 0 && (
          <Box p={3}>
            <Grid container spacing={3}>
              <Grid item xs={12} lg={8}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" mb={2}>
                      Метрики производительности
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={performanceMetrics}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="time" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line 
                          type="monotone" 
                          dataKey="cpu" 
                          stroke="#8884d8" 
                          name="CPU %" 
                        />
                        <Line 
                          type="monotone" 
                          dataKey="memory" 
                          stroke="#82ca9d" 
                          name="Память %" 
                        />
                        <Line 
                          type="monotone" 
                          dataKey="decisions" 
                          stroke="#ffc658" 
                          name="Решения/мин" 
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} lg={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography variant="h6" mb={2}>
                      Оптимизация
                    </Typography>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={optimizationEnabled}
                          onChange={(e) => setOptimizationEnabled(e.target.checked)}
                        />
                      }
                      label="Автооптимизация"
                    />
                    
                    <Box mt={2}>
                      <Typography variant="body2" color="textSecondary" mb={1}>
                        Использование кеша
                      </Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={(knowledgeStats?.cache_hit_rate || 0) * 100} 
                        sx={{ mb: 1 }}
                      />
                      <Typography variant="body2">
                        {((knowledgeStats?.cache_hit_rate || 0) * 100).toFixed(1)}% попаданий
                      </Typography>
                    </Box>

                    <Box mt={2}>
                      <Typography variant="body2" color="textSecondary" mb={1}>
                        Эффективность памяти
                      </Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={85} 
                        color="success"
                        sx={{ mb: 1 }}
                      />
                      <Typography variant="body2">
                        85% оптимизация
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}

        {/* Вкладка решений */}
        {activeTab === 1 && (
          <Box p={3}>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Действие</TableCell>
                    <TableCell>Уверенность</TableCell>
                    <TableCell>Время</TableCell>
                    <TableCell>Статус</TableCell>
                    <TableCell>Результат</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {decisions.map((decision) => (
                    <TableRow key={decision.id}>
                      <TableCell>{decision.action}</TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          <LinearProgress
                            variant="determinate"
                            value={decision.confidence * 100}
                            sx={{ width: 60, mr: 1 }}
                          />
                          {(decision.confidence * 100).toFixed(0)}%
                        </Box>
                      </TableCell>
                      <TableCell>{decision.timestamp}</TableCell>
                      <TableCell>
                        <Chip
                          label={decision.status}
                          color={getStatusColor(decision.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={decision.outcome}
                          color={getStatusColor(decision.outcome)}
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {/* Вкладка базы знаний */}
        {activeTab === 2 && (
          <Box p={3}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" mb={2}>
                      Распределение знаний по категориям
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={Object.entries(knowledgeStats?.categories || {}).map(([name, value]) => ({
                            name,
                            value
                          }))}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {Object.entries(knowledgeStats?.categories || {}).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" mb={2}>
                      Статистика базы знаний
                    </Typography>
                    
                    <Box mb={2}>
                      <Typography variant="h4" color="primary">
                        {knowledgeStats?.total_entries || 0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Всего записей
                      </Typography>
                    </Box>

                    <Box mb={2}>
                      <Typography variant="h5" color="success.main">
                        +{knowledgeStats?.recent_growth || 0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Новых за сегодня
                      </Typography>
                    </Box>

                    <Alert severity="info" sx={{ mt: 2 }}>
                      База знаний активно пополняется новой информацией и автоматически категоризируется
                    </Alert>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}

        {/* Вкладка компонентов */}
        {activeTab === 3 && (
          <Box p={3}>
            <Grid container spacing={3}>
              {Object.entries(aiStatus?.components || {}).map(([component, status]) => (
                <Grid item xs={12} sm={6} md={3} key={component}>
                  <Card>
                    <CardContent>
                      <Box display="flex" alignItems="center" justifyContent="space-between">
                        <Typography variant="h6">
                          {component.replace('_', ' ').toUpperCase()}
                        </Typography>
                        <Chip
                          icon={status === 'active' ? <CheckCircle /> : <Error />}
                          label={status}
                          color={getStatusColor(status)}
                          size="small"
                        />
                      </Box>
                      <Typography variant="body2" color="textSecondary" mt={1}>
                        Компонент {status === 'active' ? 'работает нормально' : 'требует внимания'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>

            <Accordion sx={{ mt: 3 }}>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography variant="h6">Детальная конфигурация</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Автоматическое принятие решений"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Машинное обучение"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Накопление знаний"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={<Switch checked={optimizationEnabled} onChange={(e) => setOptimizationEnabled(e.target.checked)} />}
                      label="Оптимизация производительности"
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Box>
        )}
      </Card>

      {/* Диалог конфигурации */}
      <Dialog open={configDialog} onClose={() => setConfigDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Настройки ИИ-системы</DialogTitle>
        <DialogContent>
          <TextField
            label="Интервал принятия решений (сек)"
            type="number"
            defaultValue={30}
            fullWidth
            margin="normal"
          />
          <TextField
            label="Интервал обучения (сек)"
            type="number"
            defaultValue={60}
            fullWidth
            margin="normal"
          />
          <TextField
            label="Порог уверенности"
            type="number"
            defaultValue={0.7}
            inputProps={{ min: 0, max: 1, step: 0.1 }}
            fullWidth
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialog(false)}>Отмена</Button>
          <Button onClick={() => setConfigDialog(false)} variant="contained">
            Сохранить
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AIDashboard;