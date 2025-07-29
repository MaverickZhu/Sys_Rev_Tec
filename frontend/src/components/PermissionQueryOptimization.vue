<template>
  <div class="permission-query-optimization">
    <el-card class="header-card">
      <div slot="header" class="clearfix">
        <span class="card-title">权限查询性能优化</span>
        <el-button-group style="float: right;">
          <el-button 
            type="primary" 
            icon="el-icon-refresh" 
            @click="refreshData"
            :loading="loading"
          >
            刷新数据
          </el-button>
          <el-button 
            type="warning" 
            icon="el-icon-setting" 
            @click="showConfigDialog = true"
          >
            优化配置
          </el-button>
        </el-button-group>
      </div>
      
      <!-- 系统健康状态 -->
      <div class="health-status">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="status-item">
              <div class="status-icon" :class="healthStatus.status === 'healthy' ? 'healthy' : 'unhealthy'">
                <i :class="healthStatus.status === 'healthy' ? 'el-icon-success' : 'el-icon-error'"></i>
              </div>
              <div class="status-text">
                <div class="status-title">系统状态</div>
                <div class="status-value">{{ healthStatus.status === 'healthy' ? '正常' : '异常' }}</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="status-item">
              <div class="status-icon query-optimizer">
                <i class="el-icon-search"></i>
              </div>
              <div class="status-text">
                <div class="status-title">查询优化器</div>
                <div class="status-value">{{ healthStatus.components?.query_optimizer?.total_queries || 0 }} 次查询</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="status-item">
              <div class="status-icon batch-checker">
                <i class="el-icon-files"></i>
              </div>
              <div class="status-text">
                <div class="status-title">批量检查器</div>
                <div class="status-value">{{ healthStatus.components?.batch_checker?.total_batch_checks || 0 }} 次批量检查</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="status-item">
              <div class="status-icon preloader">
                <i class="el-icon-loading"></i>
              </div>
              <div class="status-text">
                <div class="status-title">预加载器</div>
                <div class="status-value">{{ healthStatus.components?.preloader?.total_requests || 0 }} 次预加载</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 功能选项卡 -->
    <el-tabs v-model="activeTab" type="card" class="optimization-tabs">
      <!-- 批量权限检查 -->
      <el-tab-pane label="批量权限检查" name="batch-check">
        <el-card>
          <div slot="header">
            <span>批量权限检查</span>
            <el-button 
              style="float: right; padding: 3px 0" 
              type="text" 
              @click="showBatchCheckDialog = true"
            >
              新建检查
            </el-button>
          </div>
          
          <!-- 批量检查统计 -->
          <div class="stats-section">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-statistic title="总检查次数" :value="batchCheckStats.total_batch_checks || 0"></el-statistic>
              </el-col>
              <el-col :span="8">
                <el-statistic title="平均执行时间" :value="batchCheckStats.avg_execution_time || 0" suffix="ms"></el-statistic>
              </el-col>
              <el-col :span="8">
                <el-statistic title="缓存命中率" :value="(batchCheckStats.cache_hit_rate * 100).toFixed(1) || 0" suffix="%"></el-statistic>
              </el-col>
            </el-row>
          </div>
          
          <!-- 最近检查记录 -->
          <div class="recent-checks">
            <h4>最近检查记录</h4>
            <el-table :data="recentBatchChecks" stripe>
              <el-table-column prop="timestamp" label="时间" width="180">
                <template slot-scope="scope">
                  {{ formatTime(scope.row.timestamp) }}
                </template>
              </el-table-column>
              <el-table-column prop="user_count" label="用户数" width="100"></el-table-column>
              <el-table-column prop="permission_count" label="权限数" width="100"></el-table-column>
              <el-table-column prop="execution_time" label="执行时间" width="120">
                <template slot-scope="scope">
                  {{ scope.row.execution_time }}ms
                </template>
              </el-table-column>
              <el-table-column prop="cache_hit_rate" label="缓存命中率" width="120">
                <template slot-scope="scope">
                  {{ (scope.row.cache_hit_rate * 100).toFixed(1) }}%
                </template>
              </el-table-column>
              <el-table-column prop="mode" label="检查模式" width="100"></el-table-column>
              <el-table-column prop="strategy" label="检查策略" width="120"></el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 权限预加载 -->
      <el-tab-pane label="权限预加载" name="preload">
        <el-card>
          <div slot="header">
            <span>权限预加载管理</span>
            <el-button-group style="float: right;">
              <el-button 
                type="primary" 
                size="small" 
                @click="showPreloadDialog = true"
              >
                手动预加载
              </el-button>
              <el-button 
                type="success" 
                size="small" 
                @click="autoPreload"
                :loading="autoPreloadLoading"
              >
                自动预加载
              </el-button>
            </el-button-group>
          </div>
          
          <!-- 预加载统计 -->
          <div class="stats-section">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-statistic title="总预加载请求" :value="preloadStats.total_requests || 0"></el-statistic>
              </el-col>
              <el-col :span="6">
                <el-statistic title="成功预加载" :value="preloadStats.successful_preloads || 0"></el-statistic>
              </el-col>
              <el-col :span="6">
                <el-statistic title="队列中请求" :value="preloadStats.pending_requests || 0"></el-statistic>
              </el-col>
              <el-col :span="6">
                <el-statistic title="预加载命中率" :value="(preloadStats.hit_rate * 100).toFixed(1) || 0" suffix="%"></el-statistic>
              </el-col>
            </el-row>
          </div>
          
          <!-- 访问模式分析 -->
          <div class="access-patterns">
            <h4>访问模式分析</h4>
            <el-table :data="accessPatterns" stripe>
              <el-table-column prop="user_id" label="用户ID" width="100"></el-table-column>
              <el-table-column prop="access_frequency" label="访问频率" width="120"></el-table-column>
              <el-table-column prop="last_access" label="最后访问" width="180">
                <template slot-scope="scope">
                  {{ formatTime(scope.row.last_access) }}
                </template>
              </el-table-column>
              <el-table-column prop="frequent_permissions" label="常用权限">
                <template slot-scope="scope">
                  <el-tag 
                    v-for="permission in scope.row.frequent_permissions.slice(0, 3)" 
                    :key="permission" 
                    size="mini" 
                    style="margin-right: 5px;"
                  >
                    {{ permission }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                <template slot-scope="scope">
                  <el-button 
                    type="text" 
                    size="small" 
                    @click="preloadUser(scope.row.user_id)"
                  >
                    预加载
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 性能分析 -->
      <el-tab-pane label="性能分析" name="performance">
        <el-card>
          <div slot="header">
            <span>权限使用分析</span>
            <el-select 
              v-model="analysisDays" 
              style="float: right; width: 120px;" 
              @change="loadUsageAnalysis"
            >
              <el-option label="7天" :value="7"></el-option>
              <el-option label="30天" :value="30"></el-option>
              <el-option label="90天" :value="90"></el-option>
            </el-select>
          </div>
          
          <!-- 使用分析图表 -->
          <div class="analysis-charts">
            <el-row :gutter="20">
              <el-col :span="12">
                <div class="chart-container">
                  <h4>权限使用频率 TOP 10</h4>
                  <div id="permission-usage-chart" style="height: 300px;"></div>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="chart-container">
                  <h4>角色使用频率 TOP 10</h4>
                  <div id="role-usage-chart" style="height: 300px;"></div>
                </div>
              </el-col>
            </el-row>
          </div>
          
          <!-- 查询优化器统计 -->
          <div class="optimizer-stats">
            <h4>查询优化器统计</h4>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-statistic title="总查询次数" :value="queryOptimizerStats.total_queries || 0"></el-statistic>
              </el-col>
              <el-col :span="8">
                <el-statistic title="缓存命中次数" :value="queryOptimizerStats.cache_hits || 0"></el-statistic>
              </el-col>
              <el-col :span="8">
                <el-statistic title="数据库查询次数" :value="queryOptimizerStats.db_queries || 0"></el-statistic>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 索引优化 -->
      <el-tab-pane label="索引优化" name="index">
        <el-card>
          <div slot="header">
            <span>数据库索引优化</span>
            <el-button 
              style="float: right;" 
              type="danger" 
              size="small" 
              @click="applyIndexOptimizations"
              :loading="applyIndexLoading"
            >
              应用优化
            </el-button>
          </div>
          
          <!-- 索引建议 -->
          <div class="index-suggestions">
            <h4>索引优化建议</h4>
            <el-table :data="indexSuggestions" stripe>
              <el-table-column prop="table_name" label="表名" width="150"></el-table-column>
              <el-table-column prop="index_name" label="索引名" width="200"></el-table-column>
              <el-table-column prop="columns" label="索引列">
                <template slot-scope="scope">
                  <el-tag 
                    v-for="column in scope.row.columns" 
                    :key="column" 
                    size="mini" 
                    style="margin-right: 5px;"
                  >
                    {{ column }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="reason" label="优化原因"></el-table-column>
              <el-table-column prop="priority" label="优先级" width="100">
                <template slot-scope="scope">
                  <el-tag 
                    :type="scope.row.priority === 'high' ? 'danger' : scope.row.priority === 'medium' ? 'warning' : 'info'"
                    size="mini"
                  >
                    {{ scope.row.priority }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 批量检查对话框 -->
    <el-dialog title="批量权限检查" :visible.sync="showBatchCheckDialog" width="600px">
      <el-form :model="batchCheckForm" label-width="120px">
        <el-form-item label="用户ID列表">
          <el-input 
            v-model="batchCheckForm.userIds" 
            type="textarea" 
            :rows="3" 
            placeholder="请输入用户ID，用逗号分隔"
          ></el-input>
        </el-form-item>
        <el-form-item label="权限代码列表">
          <el-input 
            v-model="batchCheckForm.permissionCodes" 
            type="textarea" 
            :rows="3" 
            placeholder="请输入权限代码，用逗号分隔"
          ></el-input>
        </el-form-item>
        <el-form-item label="检查模式">
          <el-select v-model="batchCheckForm.mode" style="width: 100%;">
            <el-option label="快速模式" value="fast"></el-option>
            <el-option label="精确模式" value="accurate"></el-option>
            <el-option label="平衡模式" value="balanced"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="检查策略">
          <el-select v-model="batchCheckForm.strategy" style="width: 100%;">
            <el-option label="并行处理" value="parallel"></el-option>
            <el-option label="顺序处理" value="sequential"></el-option>
            <el-option label="批量优化" value="batch_optimized"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="batchCheckForm.useCache">使用缓存</el-checkbox>
          <el-checkbox v-model="batchCheckForm.preloadMissing">预加载缺失数据</el-checkbox>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="showBatchCheckDialog = false">取消</el-button>
        <el-button type="primary" @click="executeBatchCheck" :loading="batchCheckLoading">执行检查</el-button>
      </div>
    </el-dialog>

    <!-- 预加载对话框 -->
    <el-dialog title="手动预加载" :visible.sync="showPreloadDialog" width="500px">
      <el-form :model="preloadForm" label-width="120px">
        <el-form-item label="用户ID列表">
          <el-input 
            v-model="preloadForm.userIds" 
            type="textarea" 
            :rows="3" 
            placeholder="请输入用户ID，用逗号分隔"
          ></el-input>
        </el-form-item>
        <el-form-item label="权限代码列表">
          <el-input 
            v-model="preloadForm.permissionCodes" 
            type="textarea" 
            :rows="3" 
            placeholder="请输入权限代码，用逗号分隔（可选）"
          ></el-input>
        </el-form-item>
        <el-form-item label="优先级">
          <el-slider 
            v-model="preloadForm.priority" 
            :min="1" 
            :max="5" 
            show-stops 
            show-input
          ></el-slider>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="showPreloadDialog = false">取消</el-button>
        <el-button type="primary" @click="executePreload" :loading="preloadLoading">开始预加载</el-button>
      </div>
    </el-dialog>

    <!-- 优化配置对话框 -->
    <el-dialog title="优化配置" :visible.sync="showConfigDialog" width="600px">
      <el-form :model="configForm" label-width="150px">
        <el-form-item label="最大批量大小">
          <el-input-number v-model="configForm.max_batch_size" :min="1" :max="10000"></el-input-number>
        </el-form-item>
        <el-form-item label="每批最大用户数">
          <el-input-number v-model="configForm.max_users_per_batch" :min="1" :max="1000"></el-input-number>
        </el-form-item>
        <el-form-item label="每批最大权限数">
          <el-input-number v-model="configForm.max_permissions_per_batch" :min="1" :max="1000"></el-input-number>
        </el-form-item>
        <el-form-item label="缓存TTL（秒）">
          <el-input-number v-model="configForm.cache_ttl" :min="60" :max="86400"></el-input-number>
        </el-form-item>
        <el-form-item label="并行处理阈值">
          <el-input-number v-model="configForm.parallel_threshold" :min="1" :max="1000"></el-input-number>
        </el-form-item>
        <el-form-item label="优化级别">
          <el-select v-model="configForm.optimization_level" style="width: 100%;">
            <el-option label="基础优化" :value="1"></el-option>
            <el-option label="标准优化" :value="2"></el-option>
            <el-option label="高级优化" :value="3"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="configForm.enable_preloading">启用预加载</el-checkbox>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="showConfigDialog = false">取消</el-button>
        <el-button type="primary" @click="updateConfig" :loading="configLoading">保存配置</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { permissionQueryOptimizationApi } from '@/api/permission-query-optimization'

export default {
  name: 'PermissionQueryOptimization',
  data() {
    return {
      loading: false,
      activeTab: 'batch-check',
      
      // 健康状态
      healthStatus: {
        status: 'healthy',
        components: {}
      },
      
      // 批量检查相关
      showBatchCheckDialog: false,
      batchCheckLoading: false,
      batchCheckStats: {},
      recentBatchChecks: [],
      batchCheckForm: {
        userIds: '',
        permissionCodes: '',
        mode: 'balanced',
        strategy: 'batch_optimized',
        useCache: true,
        preloadMissing: true
      },
      
      // 预加载相关
      showPreloadDialog: false,
      preloadLoading: false,
      autoPreloadLoading: false,
      preloadStats: {},
      accessPatterns: [],
      preloadForm: {
        userIds: '',
        permissionCodes: '',
        priority: 3
      },
      
      // 性能分析相关
      analysisDays: 30,
      usageAnalysis: {},
      queryOptimizerStats: {},
      
      // 索引优化相关
      indexSuggestions: [],
      applyIndexLoading: false,
      
      // 配置相关
      showConfigDialog: false,
      configLoading: false,
      configForm: {
        max_batch_size: 1000,
        max_users_per_batch: 100,
        max_permissions_per_batch: 50,
        cache_ttl: 3600,
        enable_preloading: true,
        parallel_threshold: 10,
        optimization_level: 2
      }
    }
  },
  
  mounted() {
    this.initData()
  },
  
  methods: {
    async initData() {
      this.loading = true
      try {
        await Promise.all([
          this.loadHealthStatus(),
          this.loadBatchCheckStats(),
          this.loadPreloadStats(),
          this.loadQueryOptimizerStats(),
          this.loadIndexSuggestions(),
          this.loadAccessPatterns(),
          this.loadUsageAnalysis()
        ])
      } catch (error) {
        console.error('初始化数据失败:', error)
        this.$message.error('初始化数据失败')
      } finally {
        this.loading = false
      }
    },
    
    async refreshData() {
      await this.initData()
      this.$message.success('数据已刷新')
    },
    
    // 健康状态检查
    async loadHealthStatus() {
      try {
        const response = await permissionQueryOptimizationApi.getHealthStatus()
        if (response.success) {
          this.healthStatus = response.data
        }
      } catch (error) {
        console.error('获取健康状态失败:', error)
      }
    },
    
    // 批量检查相关方法
    async loadBatchCheckStats() {
      try {
        const response = await permissionQueryOptimizationApi.getBatchCheckStats()
        if (response.success) {
          this.batchCheckStats = response.data
          // 模拟最近检查记录
          this.recentBatchChecks = response.data.recent_checks || []
        }
      } catch (error) {
        console.error('获取批量检查统计失败:', error)
      }
    },
    
    async executeBatchCheck() {
      if (!this.batchCheckForm.userIds.trim() || !this.batchCheckForm.permissionCodes.trim()) {
        this.$message.error('请输入用户ID和权限代码')
        return
      }
      
      this.batchCheckLoading = true
      try {
        const userIds = this.batchCheckForm.userIds.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id))
        const permissionCodes = this.batchCheckForm.permissionCodes.split(',').map(code => code.trim()).filter(code => code)
        
        const response = await permissionQueryOptimizationApi.batchCheckPermissions({
          user_ids: userIds,
          permission_codes: permissionCodes,
          mode: this.batchCheckForm.mode,
          strategy: this.batchCheckForm.strategy,
          use_cache: this.batchCheckForm.useCache,
          preload_missing: this.batchCheckForm.preloadMissing
        })
        
        if (response.success) {
          this.$message.success(`批量检查完成，执行时间: ${response.data.execution_time}ms`)
          this.showBatchCheckDialog = false
          this.loadBatchCheckStats()
        }
      } catch (error) {
        console.error('批量检查失败:', error)
        this.$message.error('批量检查失败')
      } finally {
        this.batchCheckLoading = false
      }
    },
    
    // 预加载相关方法
    async loadPreloadStats() {
      try {
        const response = await permissionQueryOptimizationApi.getPreloadStats()
        if (response.success) {
          this.preloadStats = response.data
        }
      } catch (error) {
        console.error('获取预加载统计失败:', error)
      }
    },
    
    async loadAccessPatterns() {
      try {
        const response = await permissionQueryOptimizationApi.getAccessPatterns()
        if (response.success) {
          this.accessPatterns = response.data.patterns || []
        }
      } catch (error) {
        console.error('获取访问模式失败:', error)
      }
    },
    
    async executePreload() {
      if (!this.preloadForm.userIds.trim()) {
        this.$message.error('请输入用户ID')
        return
      }
      
      this.preloadLoading = true
      try {
        const userIds = this.preloadForm.userIds.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id))
        const permissionCodes = this.preloadForm.permissionCodes ? 
          this.preloadForm.permissionCodes.split(',').map(code => code.trim()).filter(code => code) : null
        
        const response = await permissionQueryOptimizationApi.requestPreload({
          user_ids: userIds,
          permission_codes: permissionCodes,
          priority: this.preloadForm.priority
        })
        
        if (response.success) {
          this.$message.success('预加载请求已提交')
          this.showPreloadDialog = false
          this.loadPreloadStats()
        }
      } catch (error) {
        console.error('预加载失败:', error)
        this.$message.error('预加载失败')
      } finally {
        this.preloadLoading = false
      }
    },
    
    async autoPreload() {
      this.autoPreloadLoading = true
      try {
        const response = await permissionQueryOptimizationApi.autoPreload()
        if (response.success) {
          this.$message.success('自动预加载完成')
          this.loadPreloadStats()
        }
      } catch (error) {
        console.error('自动预加载失败:', error)
        this.$message.error('自动预加载失败')
      } finally {
        this.autoPreloadLoading = false
      }
    },
    
    async preloadUser(userId) {
      try {
        const response = await permissionQueryOptimizationApi.requestPreload({
          user_ids: [userId],
          priority: 2
        })
        
        if (response.success) {
          this.$message.success(`用户 ${userId} 预加载请求已提交`)
        }
      } catch (error) {
        console.error('用户预加载失败:', error)
        this.$message.error('用户预加载失败')
      }
    },
    
    // 性能分析相关方法
    async loadQueryOptimizerStats() {
      try {
        const response = await permissionQueryOptimizationApi.getQueryOptimizerStats()
        if (response.success) {
          this.queryOptimizerStats = response.data.query_stats
        }
      } catch (error) {
        console.error('获取查询优化器统计失败:', error)
      }
    },
    
    async loadUsageAnalysis() {
      try {
        const response = await permissionQueryOptimizationApi.getUsageAnalysis(this.analysisDays)
        if (response.success) {
          this.usageAnalysis = response.data
          this.$nextTick(() => {
            this.renderUsageCharts()
          })
        }
      } catch (error) {
        console.error('获取使用分析失败:', error)
      }
    },
    
    renderUsageCharts() {
      // 权限使用频率图表
      const permissionChart = echarts.init(document.getElementById('permission-usage-chart'))
      const permissionData = this.usageAnalysis.permission_usage || []
      
      permissionChart.setOption({
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        xAxis: {
          type: 'category',
          data: permissionData.map(item => item.permission_code),
          axisLabel: {
            rotate: 45
          }
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          data: permissionData.map(item => item.usage_count),
          type: 'bar',
          itemStyle: {
            color: '#409EFF'
          }
        }]
      })
      
      // 角色使用频率图表
      const roleChart = echarts.init(document.getElementById('role-usage-chart'))
      const roleData = this.usageAnalysis.role_usage || []
      
      roleChart.setOption({
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        xAxis: {
          type: 'category',
          data: roleData.map(item => item.role_name),
          axisLabel: {
            rotate: 45
          }
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          data: roleData.map(item => item.usage_count),
          type: 'bar',
          itemStyle: {
            color: '#67C23A'
          }
        }]
      })
    },
    
    // 索引优化相关方法
    async loadIndexSuggestions() {
      try {
        const response = await permissionQueryOptimizationApi.getIndexSuggestions()
        if (response.success) {
          this.indexSuggestions = response.data.suggestions
        }
      } catch (error) {
        console.error('获取索引建议失败:', error)
      }
    },
    
    async applyIndexOptimizations() {
      this.$confirm('应用索引优化将修改数据库结构，是否继续？', '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        this.applyIndexLoading = true
        try {
          const response = await permissionQueryOptimizationApi.applyIndexOptimizations()
          if (response.success) {
            this.$message.success('索引优化应用成功')
            this.loadIndexSuggestions()
          }
        } catch (error) {
          console.error('应用索引优化失败:', error)
          this.$message.error('应用索引优化失败')
        } finally {
          this.applyIndexLoading = false
        }
      })
    },
    
    // 配置相关方法
    async updateConfig() {
      this.configLoading = true
      try {
        const response = await permissionQueryOptimizationApi.updateConfig(this.configForm)
        if (response.success) {
          this.$message.success('配置更新成功')
          this.showConfigDialog = false
        }
      } catch (error) {
        console.error('更新配置失败:', error)
        this.$message.error('更新配置失败')
      } finally {
        this.configLoading = false
      }
    },
    
    // 工具方法
    formatTime(timestamp) {
      if (!timestamp) return '-'
      return new Date(timestamp).toLocaleString()
    }
  }
}
</script>

<style scoped>
.permission-query-optimization {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.card-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.health-status {
  margin-top: 20px;
}

.status-item {
  display: flex;
  align-items: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.status-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 18px;
  color: white;
}

.status-icon.healthy {
  background-color: #67C23A;
}

.status-icon.unhealthy {
  background-color: #F56C6C;
}

.status-icon.query-optimizer {
  background-color: #409EFF;
}

.status-icon.batch-checker {
  background-color: #E6A23C;
}

.status-icon.preloader {
  background-color: #909399;
}

.status-text {
  flex: 1;
}

.status-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.status-value {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.optimization-tabs {
  margin-top: 20px;
}

.stats-section {
  margin-bottom: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.recent-checks {
  margin-top: 20px;
}

.access-patterns {
  margin-top: 20px;
}

.analysis-charts {
  margin-bottom: 30px;
}

.chart-container {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.chart-container h4 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 14px;
}

.optimizer-stats {
  margin-top: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.index-suggestions {
  margin-top: 20px;
}

.el-statistic {
  text-align: center;
}

.el-dialog .el-form {
  padding: 0 20px;
}

.el-table {
  margin-top: 15px;
}

.el-tag {
  margin-right: 5px;
  margin-bottom: 5px;
}

.clearfix:before,
.clearfix:after {
  display: table;
  content: "";
}

.clearfix:after {
  clear: both;
}
</style>