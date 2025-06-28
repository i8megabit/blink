import React, { useState, useEffect } from 'react';
import { useNotifications } from '../hooks/useNotifications';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { Input } from './ui/Input';
import { Progress } from './ui/Progress';

interface Test {
  id: string;
  name: string;
  description: string;
  test_type: 'unit' | 'api' | 'performance' | 'seo' | 'llm' | 'generic';
  priority: 'low' | 'medium' | 'high' | 'critical';
  environment: 'development' | 'staging' | 'production';
  status: 'pending' | 'running' | 'passed' | 'failed' | 'error' | 'cancelled';
  created_at: string;
  updated_at: string;
  tags: string[];
  metadata: Record<string, any>;
}

interface TestExecution {
  id: string;
  test_request: any;
  status: 'pending' | 'running' | 'passed' | 'failed' | 'error' | 'cancelled';
  progress: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  results: any[];
  user_id: number;
  metadata: Record<string, any>;
}

interface TestMetrics {
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  success_rate: number;
  average_duration: number;
  total_executions: number;
  running_executions: number;
}

const Testing: React.FC = () => {
  const [tests, setTests] = useState<Test[]>([]);
  const [executions, setExecutions] = useState<TestExecution[]>([]);
  const [metrics, setMetrics] = useState<TestMetrics | null>(null);
  // const [selectedTest, setSelectedTest] = useState<Test | null>(null);
  const [isCreatingTest, setIsCreatingTest] = useState(false); 