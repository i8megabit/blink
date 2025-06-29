import React, { useState, useEffect } from 'react';
import { Card, Button, Badge, Input, Textarea, Modal, Table, Tag } from './ui';

interface CollectionInfo {
  name: string;
  created_at: number;
  updated_at: number;
  versions: CollectionVersion[];
  current_version?: string;
  metadata?: Record<string, any>;
}

interface CollectionVersion {
  version_id: string;
  timestamp: number;
  description?: string;
  data_hash?: string;
}

interface CollectionsManagerProps {
  routerUrl?: string;
}

export const CollectionsManager: React.FC<CollectionsManagerProps> = ({
  routerUrl = 'http://localhost:8004'
}) => {
  const [collections, setCollections] = useState<CollectionInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showVersionModal, setShowVersionModal] = useState(false);
  const [selectedCollection, setSelectedCollection] = useState<string>('');
  const [newCollection, setNewCollection] = useState({
    name: '',
    description: '',
    metadata: ''
  });

  useEffect(() => {
    loadCollections();
  }, []);

  const loadCollections = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${routerUrl}/api/v1/collections`);
      if (response.ok) {
        const data = await response.json();
        setCollections(data);
      }
    } catch (error) {
      console.error('Ошибка загрузки коллекций:', error);
    } finally {
      setLoading(false);
    }
  };

  const createCollection = async () => {
    try {
      const metadata = newCollection.metadata ? JSON.parse(newCollection.metadata) : {};
      
      const response = await fetch(`${routerUrl}/api/v1/collections`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newCollection.name,
          description: newCollection.description,
          metadata
        })
      });

      if (response.ok) {
        setShowCreateModal(false);
        setNewCollection({ name: '', description: '', metadata: '' });
        loadCollections();
      }
    } catch (error) {
      console.error('Ошибка создания коллекции:', error);
    }
  };

  const deleteCollection = async (name: string) => {
    if (!confirm(`Удалить коллекцию "${name}"?`)) return;

    try {
      const response = await fetch(`${routerUrl}/api/v1/collections/${name}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        loadCollections();
      }
    } catch (error) {
      console.error('Ошибка удаления коллекции:', error);
    }
  };

  const createVersion = async () => {
    try {
      const response = await fetch(`${routerUrl}/api/v1/collections/${selectedCollection}/version`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description: `Version created at ${new Date().toISOString()}`
        })
      });

      if (response.ok) {
        setShowVersionModal(false);
        loadCollections();
      }
    } catch (error) {
      console.error('Ошибка создания версии:', error);
    }
  };

  const rollbackToVersion = async (collectionName: string, versionId: string) => {
    if (!confirm(`Откатиться к версии ${versionId}?`)) return;

    try {
      const response = await fetch(`${routerUrl}/api/v1/collections/${collectionName}/rollback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ version_id: versionId })
      });

      if (response.ok) {
        loadCollections();
      }
    } catch (error) {
      console.error('Ошибка отката версии:', error);
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Управление коллекциями</h2>
        <Button onClick={() => setShowCreateModal(true)}>
          Создать коллекцию
        </Button>
      </div>

      {loading ? (
        <div className="text-center py-8">Загрузка коллекций...</div>
      ) : (
        <div className="grid gap-4">
          {collections.map((collection) => (
            <Card key={collection.name} className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold">{collection.name}</h3>
                  <p className="text-gray-600 text-sm">
                    Создана: {formatDate(collection.created_at)}
                  </p>
                  <p className="text-gray-600 text-sm">
                    Обновлена: {formatDate(collection.updated_at)}
                  </p>
                  {collection.description && (
                    <p className="text-gray-700 mt-2">{collection.description}</p>
                  )}
                </div>
                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setSelectedCollection(collection.name);
                      setShowVersionModal(true);
                    }}
                  >
                    Создать версию
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => deleteCollection(collection.name)}
                  >
                    Удалить
                  </Button>
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="font-medium">Версии:</h4>
                <div className="space-y-2">
                  {collection.versions.map((version) => (
                    <div
                      key={version.version_id}
                      className="flex justify-between items-center p-3 bg-gray-50 rounded"
                    >
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-sm">{version.version_id}</span>
                          {collection.current_version === version.version_id && (
                            <Badge variant="success">Текущая</Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-600">
                          {formatDate(version.timestamp)}
                        </p>
                        {version.description && (
                          <p className="text-sm text-gray-700">{version.description}</p>
                        )}
                      </div>
                      {collection.current_version !== version.version_id && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => rollbackToVersion(collection.name, version.version_id)}
                        >
                          Откатиться
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Модальное окно создания коллекции */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Создать коллекцию"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Название</label>
            <Input
              value={newCollection.name}
              onChange={(e) => setNewCollection({ ...newCollection, name: e.target.value })}
              placeholder="Введите название коллекции"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Описание</label>
            <Textarea
              value={newCollection.description}
              onChange={(e) => setNewCollection({ ...newCollection, description: e.target.value })}
              placeholder="Описание коллекции"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Метаданные (JSON)</label>
            <Textarea
              value={newCollection.metadata}
              onChange={(e) => setNewCollection({ ...newCollection, metadata: e.target.value })}
              placeholder='{"key": "value"}'
            />
          </div>
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
              Отмена
            </Button>
            <Button onClick={createCollection}>Создать</Button>
          </div>
        </div>
      </Modal>

      {/* Модальное окно создания версии */}
      <Modal
        isOpen={showVersionModal}
        onClose={() => setShowVersionModal(false)}
        title={`Создать версию для ${selectedCollection}`}
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Создать новую версию коллекции "{selectedCollection}"?
          </p>
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setShowVersionModal(false)}>
              Отмена
            </Button>
            <Button onClick={createVersion}>Создать версию</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}; 