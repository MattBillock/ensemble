import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Spinner, Badge, ProgressBar, Form } from 'react-bootstrap';
import {
  getAllAchievements,
  getRecentAchievements,
  getAchievementStats
} from '../services/api';

function AchievementsDashboard() {
  const [loading, setLoading] = useState(true);
  const [achievements, setAchievements] = useState([]);
  const [recent, setRecent] = useState([]);
  const [stats, setStats] = useState(null);
  const [filter, setFilter] = useState('all');
  const [showUnlocked, setShowUnlocked] = useState('all'); // all, unlocked, locked

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [achievementsRes, recentRes, statsRes] = await Promise.all([
        getAllAchievements(),
        getRecentAchievements(20),
        getAchievementStats()
      ]);
      setAchievements(achievementsRes.achievements || []);
      setRecent(recentRes.achievements || []);
      setStats(statsRes);
    } catch (error) {
      console.error('Failed to fetch achievements:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRarityColor = (rarity) => {
    const colors = {
      common: '#9ca3af',
      uncommon: '#10b981',
      rare: '#3b82f6',
      epic: '#a855f7',
      legendary: '#f59e0b'
    };
    return colors[rarity] || '#9ca3af';
  };

  const getRarityBadge = (rarity) => {
    const variants = {
      common: 'secondary',
      uncommon: 'success',
      rare: 'primary',
      epic: 'info',
      legendary: 'warning'
    };
    return <Badge bg={variants[rarity] || 'secondary'}>{rarity}</Badge>;
  };

  const getCategoryBadge = (category) => {
    const icons = {
      productivity: '📈',
      comedy: '😂',
      milestone: '🏆',
      streak: '🔥',
      meta: '🤖',
      ska: '🎺'
    };
    return (
      <Badge bg="dark" className="me-1">
        {icons[category] || '❓'} {category}
      </Badge>
    );
  };

  const filteredAchievements = achievements.filter(a => {
    if (filter !== 'all' && a.category !== filter) return false;
    if (showUnlocked === 'unlocked' && !a.unlocked) return false;
    if (showUnlocked === 'locked' && a.unlocked) return false;
    return true;
  });

  const unlockedCount = achievements.filter(a => a.unlocked).length;
  const totalPoints = achievements.filter(a => a.unlocked).reduce((sum, a) => sum + a.points, 0);

  if (loading) {
    return (
      <Container className="mt-5 text-center">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3">Loading achievements...</p>
      </Container>
    );
  }

  return (
    <Container fluid className="mt-4">
      <Row className="mb-4">
        <Col>
          <h2>🏆 Achievements</h2>
          <p className="text-muted">
            Pick it up! Pick it up! Your agents earn achievements for completing tasks,
            reaching milestones, and exhibiting quirky behaviors.
          </p>
        </Col>
      </Row>

      {/* Summary Cards */}
      <Row className="mb-4">
        <Col md={3}>
          <Card bg="primary" text="white">
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Unlocked
              </h6>
              <h3 className="mb-0">{unlockedCount} / {achievements.length}</h3>
              <ProgressBar
                now={achievements.length > 0 ? (unlockedCount / achievements.length) * 100 : 0}
                className="mt-2"
                variant="light"
                style={{ height: '6px' }}
              />
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card bg="warning" text="dark">
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Total Points
              </h6>
              <h3 className="mb-0">{totalPoints}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card bg="success" text="white">
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Total Awarded
              </h6>
              <h3 className="mb-0">{stats?.total_achievements_awarded || 0}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card style={{ backgroundColor: '#f59e0b' }} text="dark">
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Legendary Unlocked
              </h6>
              <h3 className="mb-0">{stats?.by_rarity?.legendary || 0}</h3>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="mb-4">
        {/* Recent Achievements */}
        <Col md={4}>
          <Card>
            <Card.Header>
              <strong>🎉 Recent Unlocks</strong>
            </Card.Header>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {recent.length === 0 ? (
                <p className="text-muted text-center py-4">
                  No achievements unlocked yet. Start running tasks!
                </p>
              ) : (
                recent.map((a, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '10px',
                      marginBottom: '8px',
                      backgroundColor: '#f8f9fa',
                      borderRadius: '8px',
                      borderLeft: `4px solid ${getRarityColor(a.rarity)}`
                    }}
                  >
                    <div style={{ fontSize: '1.5rem', display: 'inline-block', marginRight: '8px' }}>
                      {a.icon}
                    </div>
                    <strong>{a.name}</strong>
                    <br />
                    <small className="text-muted">
                      {a.agent_name} - {new Date(a.awarded_at).toLocaleDateString()}
                    </small>
                  </div>
                ))
              )}
            </Card.Body>
          </Card>
        </Col>

        {/* Stats by Category */}
        <Col md={4}>
          <Card>
            <Card.Header>
              <strong>📊 By Category</strong>
            </Card.Header>
            <Card.Body>
              {Object.entries(stats?.by_category || {}).map(([cat, count]) => (
                <div key={cat} className="mb-2">
                  <div className="d-flex justify-content-between align-items-center mb-1">
                    {getCategoryBadge(cat)}
                    <span>{count}</span>
                  </div>
                  <ProgressBar
                    now={(count / Math.max(stats?.total_achievements_awarded || 1, 1)) * 100}
                    variant="info"
                    style={{ height: '6px' }}
                  />
                </div>
              ))}
            </Card.Body>
          </Card>
        </Col>

        {/* Top Agents */}
        <Col md={4}>
          <Card>
            <Card.Header>
              <strong>⭐ Top Achievers</strong>
            </Card.Header>
            <Card.Body>
              {(stats?.top_agents || []).length === 0 ? (
                <p className="text-muted text-center py-4">No data yet</p>
              ) : (
                <Table hover size="sm" className="mb-0">
                  <thead>
                    <tr>
                      <th>Agent</th>
                      <th className="text-end">Achievements</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(stats?.top_agents || []).map((agent, idx) => (
                      <tr key={idx}>
                        <td><code>{agent.agent}</code></td>
                        <td className="text-end">
                          <Badge bg="primary">{agent.count}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* All Achievements */}
      <Row>
        <Col>
          <Card>
            <Card.Header>
              <div className="d-flex justify-content-between align-items-center">
                <strong>📋 All Achievements</strong>
                <div className="d-flex gap-2">
                  <Form.Select
                    size="sm"
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    style={{ width: '150px' }}
                  >
                    <option value="all">All Categories</option>
                    <option value="ska">🎺 Ska</option>
                    <option value="productivity">📈 Productivity</option>
                    <option value="comedy">😂 Comedy</option>
                    <option value="milestone">🏆 Milestone</option>
                    <option value="streak">🔥 Streak</option>
                    <option value="meta">🤖 Meta</option>
                  </Form.Select>
                  <Form.Select
                    size="sm"
                    value={showUnlocked}
                    onChange={(e) => setShowUnlocked(e.target.value)}
                    style={{ width: '130px' }}
                  >
                    <option value="all">All</option>
                    <option value="unlocked">Unlocked</option>
                    <option value="locked">Locked</option>
                  </Form.Select>
                </div>
              </div>
            </Card.Header>
            <Card.Body style={{ maxHeight: '600px', overflowY: 'auto' }}>
              <Row>
                {filteredAchievements.map((achievement) => (
                  <Col md={4} key={achievement.id} className="mb-3">
                    <Card
                      style={{
                        opacity: achievement.unlocked ? 1 : 0.5,
                        borderColor: achievement.unlocked ? getRarityColor(achievement.rarity) : '#dee2e6',
                        borderWidth: '2px'
                      }}
                    >
                      <Card.Body>
                        <div className="d-flex align-items-start">
                          <div
                            style={{
                              fontSize: '2rem',
                              marginRight: '12px',
                              filter: achievement.unlocked ? 'none' : 'grayscale(100%)'
                            }}
                          >
                            {achievement.icon}
                          </div>
                          <div style={{ flex: 1 }}>
                            <h6 className="mb-1">
                              {achievement.name}
                              {achievement.unlocked && (
                                <Badge bg="success" className="ms-2" style={{ fontSize: '0.6rem' }}>
                                  ✓
                                </Badge>
                              )}
                            </h6>
                            <p className="mb-2" style={{ fontSize: '0.85rem', color: '#6c757d' }}>
                              {achievement.description}
                            </p>
                            <div className="d-flex justify-content-between align-items-center">
                              <div>
                                {getRarityBadge(achievement.rarity)}
                                {getCategoryBadge(achievement.category)}
                              </div>
                              <Badge bg="dark">{achievement.points} pts</Badge>
                            </div>
                          </div>
                        </div>
                      </Card.Body>
                    </Card>
                  </Col>
                ))}
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Fun Facts */}
      <Row className="mt-4 mb-4">
        <Col>
          <Card bg="light">
            <Card.Body>
              <h6>🎺 Ska Facts</h6>
              <p className="mb-0" style={{ fontSize: '0.875rem' }}>
                <strong>Did you know?</strong> Ska originated in Jamaica in the late 1950s,
                predating reggae and rocksteady. The name "ska" might come from the scratchy
                guitar sound or from the greeting "Skavoovie!" It's gone through three waves:
                Jamaican ska (1960s), 2-Tone (late 1970s UK), and third wave (1990s US).
                Now your AI agents are part of the fourth wave! 🎸
              </p>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default AchievementsDashboard;
