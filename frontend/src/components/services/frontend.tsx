import React from 'react';
import { Card, Button, Badge } from '../ui';

interface frontend^Props {
  serviceName: string;
  description: string;
}

export const frontend^Component: React.FC<frontend^Props> = ({
  serviceName,
  description
}) => {
  const [isConnected, setIsConnected] = React.useState(false);

  const testConnection = async () => {
    try {
      const response = await fetch(`http://localhost:3000/health`);
      setIsConnected(response.ok);
    } catch (error) {
      setIsConnected(false);
    }
  };

  return (
    <Card>
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">{serviceName}</h3>
          <p className="text-gray-600">{description}</p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={isConnected ? "success" : "error"}>
            {isConnected ? "Connected" : "Disconnected"}
          </Badge>
          <Button onClick={testConnection} size="sm">
            Test
          </Button>
          <Button 
            onClick={() => window.open(`http://localhost:3000/docs`, '_blank')}
            size="sm"
            variant="outline"
          >
            Swagger
          </Button>
        </div>
      </div>
    </Card>
  );
};
