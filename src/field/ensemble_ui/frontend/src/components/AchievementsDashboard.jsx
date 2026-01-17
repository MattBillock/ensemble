import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Container, Row, Col, Card, Table, Spinner, Badge, ProgressBar, Form, Toast, ToastContainer } from 'react-bootstrap';
import {
  getAllAchievements,
  getRecentAchievements,
  getAchievementStats
} from '../services/api';
import { generateWhimsicalName } from '../utils/whimsicalNames';

// Ska facts for rotation
const SKA_FACTS = [
  {
    title: "Origins of Ska",
    fact: "Ska originated in Jamaica in the late 1950s, predating reggae and rocksteady. The name 'ska' might come from the scratchy guitar sound or from the greeting 'Skavoovie!'"
  },
  {
    title: "Three Waves of Ska",
    fact: "Ska has gone through three waves: Jamaican ska (1960s), 2-Tone (late 1970s UK), and third wave (1990s US). Now your AI agents are part of the fourth wave!"
  },
  {
    title: "The Skank Dance",
    fact: "The 'skank' is the signature ska dance move - running in place while pumping your arms. It's all about the offbeat upstroke energy!"
  },
  {
    title: "2-Tone Records",
    fact: "The British 2-Tone movement in the late 70s combined ska with punk energy. Bands like The Specials and Madness pioneered this checkerboard-loving scene."
  },
  {
    title: "Horn Section Power",
    fact: "A proper ska band needs a horn section! Trumpet, trombone, and saxophone create that unmistakable punchy brass sound."
  },
  {
    title: "The Offbeat",
    fact: "Ska is defined by its offbeat rhythm - the guitar 'chank' or upstroke on the 2nd and 4th beats. It's the opposite of rock's downbeat emphasis."
  },
  {
    title: "Rude Boys",
    fact: "In Jamaica, 'rude boys' were young rebels who loved ska. The term became synonymous with ska culture and fashion."
  },
  {
    title: "Checkered Pattern",
    fact: "The black and white checkered pattern symbolizes ska's message of racial harmony, particularly during the 2-Tone movement."
  },
  {
    title: "Prince Buster",
    fact: "Prince Buster is one of ska's founding fathers. His song 'Al Capone' directly inspired Madness's name and sound."
  },
  {
    title: "Ska-Punk Fusion",
    fact: "Third wave ska fused with punk rock, creating bands like Operation Ivy, Rancid, and Sublime. The DIY attitude fit perfectly!"
  },
  {
    title: "Studio One",
    fact: "Studio One in Kingston, Jamaica was the birthplace of recorded ska. Producer Coxsone Dodd helped define the genre's sound."
  },
  {
    title: "Walk Don't Run",
    fact: "The original ska bands often covered American R&B songs, speeding them up and adding that distinctive offbeat guitar."
  },
];

function AchievementsDashboard() {
  const [loading, setLoading] = useState(true);
  const [achievements, setAchievements] = useState([]);
  const [recent, setRecent] = useState([]);
  const [stats, setStats] = useState(null);
  const [filter, setFilter] = useState('all');
  const [showUnlocked, setShowUnlocked] = useState('all'); // all, unlocked, locked
  const [newAchievements, setNewAchievements] = useState([]); // Toast notifications
  const [currentSkaFact, setCurrentSkaFact] = useState(0);
  const seenAchievementsRef = useRef(new Set());

  // Rotate ska facts every 15 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSkaFact(prev => (prev + 1) % SKA_FACTS.length);
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  // Poll for new achievements every 30 seconds
  useEffect(() => {
    const pollInterval = setInterval(async () => {
      try {
        const recentRes = await getRecentAchievements(20);
        const newRecent = (recentRes?.achievements || []).filter(a => a && a.id);

        // Check for new achievements we haven't seen
        const newlyEarned = newRecent.filter(a => {
          const key = `${a.id}_${a.agent_name || 'unknown'}_${a.awarded_at || 'unknown'}`;
          if (!seenAchievementsRef.current.has(key)) {
            seenAchievementsRef.current.add(key);
            return true;
          }
          return false;
        });

        // Only announce new ones (newlyEarned will be empty on first poll after seenAchievementsRef is populated)
        if (newlyEarned.length > 0) {
          setNewAchievements(prev => [...prev, ...newlyEarned]);
        }

        setRecent(newRecent);
      } catch (error) {
        console.error('Failed to poll achievements:', error);
      }
    }, 30000);

    return () => clearInterval(pollInterval);
  }, []);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [achievementsRes, recentRes, statsRes] = await Promise.all([
        getAllAchievements().catch(() => ({ achievements: [] })),
        getRecentAchievements(20).catch(() => ({ achievements: [] })),
        getAchievementStats().catch(() => ({}))
      ]);

      // Filter out any null/undefined achievements
      const validAchievements = (achievementsRes?.achievements || []).filter(a => a && a.id);
      const validRecent = (recentRes?.achievements || []).filter(a => a && a.id);

      setAchievements(validAchievements);
      setRecent(validRecent);
      setStats(statsRes || {});

      // Initialize seen achievements to prevent false notifications on load
      validRecent.forEach(a => {
        const key = `${a.id}_${a.agent_name || 'unknown'}_${a.awarded_at || 'unknown'}`;
        seenAchievementsRef.current.add(key);
      });
    } catch (error) {
      console.error('Failed to fetch achievements:', error);
      // Set empty defaults on error
      setAchievements([]);
      setRecent([]);
      setStats({});
    } finally {
      setLoading(false);
    }
  };

  // Remove a toast notification
  const dismissToast = (index) => {
    setNewAchievements(prev => prev.filter((_, i) => i !== index));
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
      ska: '🎺',
      brass_band: '🎵',
      drum_corps: '🥁',
      guitar_hero: '🎮',
      famous_mustards: '🌭',
      dungeons_dragons: '🎲',
      favorite_tacos: '🌮',
      loser_board: '🤦',
      family: '👨‍👩‍👧‍👦'
    };
    const displayNames = {
      productivity: 'Productivity',
      comedy: 'Comedy',
      milestone: 'Milestone',
      streak: 'Streak',
      meta: 'Meta',
      ska: 'Ska',
      brass_band: 'Brass Band',
      drum_corps: 'Drum Corps',
      guitar_hero: 'Guitar Hero',
      famous_mustards: 'Famous Mustards',
      dungeons_dragons: 'D&D',
      favorite_tacos: 'Tacos',
      loser_board: 'Wall of Shame',
      family: 'Family'
    };
    return (
      <Badge bg={category === 'loser_board' ? 'danger' : 'dark'} className="me-1">
        {icons[category] || '❓'} {displayNames[category] || category}
      </Badge>
    );
  };

  const filteredAchievements = achievements.filter(a => {
    if (!a || !a.id) return false;  // Filter out null/undefined achievements
    if (filter !== 'all' && a.category !== filter) return false;
    if (showUnlocked === 'unlocked' && !a.unlocked) return false;
    if (showUnlocked === 'locked' && a.unlocked) return false;
    return true;
  });

  const unlockedCount = achievements.filter(a => a && a.unlocked).length;
  const totalPoints = achievements.filter(a => a && a.unlocked).reduce((sum, a) => sum + (a.points || 0), 0);

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
              <div
                style={{
                  marginTop: '8px',
                  height: '6px',
                  backgroundColor: 'rgba(255,255,255,0.3)',
                  borderRadius: '3px',
                  overflow: 'hidden'
                }}
              >
                <div
                  style={{
                    width: `${achievements.length > 0 ? (unlockedCount / achievements.length) * 100 : 0}%`,
                    height: '100%',
                    backgroundColor: 'white',
                    borderRadius: '3px',
                    transition: 'width 0.3s ease'
                  }}
                />
              </div>
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
          <Card bg="dark" text="light">
            <Card.Header style={{ backgroundColor: '#242836', borderColor: '#3a3f52' }}>
              <strong>🎉 Recent Unlocks</strong>
            </Card.Header>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {recent.length === 0 ? (
                <p className="text-muted text-center py-4">
                  No achievements unlocked yet. Start running tasks!
                </p>
              ) : (
                recent.filter(a => a && a.name).map((a, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '10px',
                      marginBottom: '8px',
                      backgroundColor: '#1a1d29',
                      borderRadius: '8px',
                      borderLeft: `4px solid ${getRarityColor(a.rarity)}`
                    }}
                  >
                    <div style={{ fontSize: '1.5rem', display: 'inline-block', marginRight: '8px' }}>
                      {a.icon || '🏆'}
                    </div>
                    <strong style={{ color: '#f7fafc' }}>{a.name}</strong>
                    <br />
                    <small style={{ color: '#9ca3af' }}>
                      {generateWhimsicalName(a.agent_name || 'unknown')} ({(a.agent_name || '').split('/').pop()?.replace('.md', '') || 'unknown'})
                    </small>
                    <br />
                    <small style={{ color: '#6b7280' }}>
                      {a.awarded_at ? new Date(a.awarded_at).toLocaleDateString() : 'Unknown date'}
                    </small>
                  </div>
                ))
              )}
            </Card.Body>
          </Card>
        </Col>

        {/* Stats by Category */}
        <Col md={4}>
          <Card bg="dark" text="light">
            <Card.Header style={{ backgroundColor: '#242836', borderColor: '#3a3f52' }}>
              <strong>📊 By Category</strong>
            </Card.Header>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {Object.entries(stats?.by_category || {}).sort((a, b) => b[1] - a[1]).map(([cat, count]) => (
                <div key={cat} className="mb-2">
                  <div className="d-flex justify-content-between align-items-center mb-1">
                    {getCategoryBadge(cat)}
                    <span style={{ color: '#e2e8f0' }}>{count}</span>
                  </div>
                  <div style={{ height: '6px', backgroundColor: '#3a3f52', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{
                      width: `${(count / Math.max(stats?.total_achievements_awarded || 1, 1)) * 100}%`,
                      height: '100%',
                      backgroundColor: '#3b82f6',
                      borderRadius: '3px'
                    }} />
                  </div>
                </div>
              ))}
            </Card.Body>
          </Card>
        </Col>

        {/* Top Agent Types */}
        <Col md={4}>
          <Card bg="dark" text="light">
            <Card.Header style={{ backgroundColor: '#242836', borderColor: '#3a3f52' }}>
              <strong>⭐ Top Agent Types</strong>
            </Card.Header>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {(stats?.top_agents || []).length === 0 ? (
                <p className="text-muted text-center py-4">No data yet</p>
              ) : (
                <Table size="sm" className="mb-0" variant="dark">
                  <thead>
                    <tr>
                      <th style={{ color: '#9ca3af' }}>Agent Type</th>
                      <th className="text-end" style={{ color: '#9ca3af' }}>Count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(stats?.top_agents || []).slice(0, 10).map((agent, idx) => (
                      <tr key={idx}>
                        <td style={{ color: '#e2e8f0' }}>{(agent?.agent || 'unknown').split('/').pop()?.replace('.md', '') || agent?.agent || 'unknown'}</td>
                        <td className="text-end">
                          <Badge bg="primary">{agent?.count || 0}</Badge>
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

      {/* Agent Leaderboard */}
      <Row className="mb-4">
        <Col md={6}>
          <Card bg="dark" text="light">
            <Card.Header style={{ backgroundColor: '#242836', borderColor: '#3a3f52' }}>
              <strong>🏆 Agent Leaderboard - Most Achievements</strong>
            </Card.Header>
            <Card.Body style={{ maxHeight: '350px', overflowY: 'auto' }}>
              {(stats?.individual_agents_by_count || []).length === 0 ? (
                <p className="text-muted text-center py-4">No individual agent data yet</p>
              ) : (
                <Table size="sm" className="mb-0" variant="dark">
                  <thead>
                    <tr>
                      <th style={{ color: '#9ca3af', width: '40px' }}>#</th>
                      <th style={{ color: '#9ca3af' }}>Agent</th>
                      <th style={{ color: '#9ca3af' }}>Type</th>
                      <th className="text-end" style={{ color: '#9ca3af' }}>Achievements</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(stats?.individual_agents_by_count || []).slice(0, 15).map((agent, idx) => (
                      <tr key={idx}>
                        <td style={{ color: idx < 3 ? '#f59e0b' : '#6b7280', fontWeight: idx < 3 ? 'bold' : 'normal' }}>
                          {idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : idx + 1}
                        </td>
                        <td style={{ color: '#10b981', fontWeight: '500' }}>
                          {generateWhimsicalName(agent?.agent_id || agent?.agent || 'unknown')}
                        </td>
                        <td style={{ color: '#9ca3af', fontSize: '12px' }}>
                          {(agent.agent_type || agent.agent || '').split('/').pop()?.replace('.md', '')}
                        </td>
                        <td className="text-end">
                          <Badge bg="success">{agent.count}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </Card.Body>
          </Card>
        </Col>

        <Col md={6}>
          <Card bg="dark" text="light">
            <Card.Header style={{ backgroundColor: '#242836', borderColor: '#3a3f52' }}>
              <strong>💎 Agent Leaderboard - Highest Score</strong>
            </Card.Header>
            <Card.Body style={{ maxHeight: '350px', overflowY: 'auto' }}>
              {(stats?.individual_agents_by_score || []).length === 0 ? (
                <p className="text-muted text-center py-4">No individual agent data yet</p>
              ) : (
                <Table size="sm" className="mb-0" variant="dark">
                  <thead>
                    <tr>
                      <th style={{ color: '#9ca3af', width: '40px' }}>#</th>
                      <th style={{ color: '#9ca3af' }}>Agent</th>
                      <th style={{ color: '#9ca3af' }}>Type</th>
                      <th className="text-end" style={{ color: '#9ca3af' }}>Points</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(stats?.individual_agents_by_score || []).slice(0, 15).map((agent, idx) => (
                      <tr key={idx}>
                        <td style={{ color: idx < 3 ? '#f59e0b' : '#6b7280', fontWeight: idx < 3 ? 'bold' : 'normal' }}>
                          {idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : idx + 1}
                        </td>
                        <td style={{ color: '#a855f7', fontWeight: '500' }}>
                          {generateWhimsicalName(agent?.agent_id || agent?.agent || 'unknown')}
                        </td>
                        <td style={{ color: '#9ca3af', fontSize: '12px' }}>
                          {(agent.agent_type || agent.agent || '').split('/').pop()?.replace('.md', '')}
                        </td>
                        <td className="text-end">
                          <Badge bg="warning" text="dark">{agent.score || agent.points}</Badge>
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
          <Card bg="dark" text="light">
            <Card.Header style={{ backgroundColor: '#242836', borderColor: '#3a3f52' }}>
              <div className="d-flex justify-content-between align-items-center">
                <strong>📋 All Achievements</strong>
                <div className="d-flex gap-2">
                  <Form.Select
                    size="sm"
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    style={{ width: '170px' }}
                  >
                    <option value="all">All Categories</option>
                    <option value="ska">🎺 Ska</option>
                    <option value="brass_band">🎵 Brass Band</option>
                    <option value="drum_corps">🥁 Drum Corps</option>
                    <option value="guitar_hero">🎮 Guitar Hero</option>
                    <option value="dungeons_dragons">🎲 D&D</option>
                    <option value="favorite_tacos">🌮 Tacos</option>
                    <option value="famous_mustards">🌭 Mustards</option>
                    <option value="productivity">📈 Productivity</option>
                    <option value="comedy">😂 Comedy</option>
                    <option value="milestone">🏆 Milestone</option>
                    <option value="streak">🔥 Streak</option>
                    <option value="meta">🤖 Meta</option>
                    <option value="family">👨‍👩‍👧‍👦 Family</option>
                    <option value="loser_board">🤦 Wall of Shame</option>
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
                            {achievement.icon || '🏆'}
                          </div>
                          <div style={{ flex: 1 }}>
                            <h6 className="mb-1">
                              {achievement.name || 'Unknown Achievement'}
                              {achievement.unlocked && (
                                <Badge bg="success" className="ms-2" style={{ fontSize: '0.6rem' }}>
                                  ✓
                                </Badge>
                              )}
                            </h6>
                            <p className="mb-2" style={{ fontSize: '0.85rem', color: '#6c757d' }}>
                              {achievement.description || 'No description available'}
                            </p>
                            <div className="d-flex justify-content-between align-items-center">
                              <div>
                                {getRarityBadge(achievement.rarity || 'common')}
                                {getCategoryBadge(achievement.category || 'misc')}
                              </div>
                              <Badge bg="dark">{achievement.points || 0} pts</Badge>
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

      {/* Rotating Ska Facts */}
      <Row className="mt-4 mb-4">
        <Col>
          <Card bg="dark" text="light" style={{ transition: 'all 0.3s ease', border: '1px solid #3a3f52' }}>
            <Card.Body>
              <h6 style={{ color: '#f7fafc' }}>🎺 Fun Facts</h6>
              <p className="mb-0" style={{ fontSize: '0.875rem', color: '#e2e8f0' }}>
                <strong style={{ color: '#f59e0b' }}>{SKA_FACTS[currentSkaFact].title}:</strong>{' '}
                {SKA_FACTS[currentSkaFact].fact}
              </p>
              <div className="mt-2 d-flex justify-content-center gap-1">
                {SKA_FACTS.map((_, idx) => (
                  <span
                    key={idx}
                    onClick={() => setCurrentSkaFact(idx)}
                    style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: idx === currentSkaFact ? '#10b981' : '#3a3f52',
                      cursor: 'pointer',
                      transition: 'background-color 0.2s'
                    }}
                  />
                ))}
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Achievement Toast Notifications */}
      <ToastContainer position="bottom-end" className="p-3" style={{ zIndex: 9999 }}>
        {newAchievements.filter(a => a).map((achievement, index) => (
          <Toast
            key={`${achievement?.id || index}_${index}`}
            onClose={() => dismissToast(index)}
            delay={8000}
            autohide
            bg="dark"
          >
            <Toast.Header closeButton={true}>
              <span style={{ fontSize: '1.5rem', marginRight: '8px' }}>{achievement?.icon || '🏆'}</span>
              <strong className="me-auto">Achievement Unlocked!</strong>
            </Toast.Header>
            <Toast.Body className="text-white">
              <strong>{achievement?.name || 'Unknown Achievement'}</strong>
              <br />
              <small>{achievement?.description || ''}</small>
              <br />
              <Badge bg="secondary" className="mt-1">
                {achievement?.agent_name || 'unknown'}
              </Badge>
            </Toast.Body>
          </Toast>
        ))}
      </ToastContainer>
    </Container>
  );
}

export default AchievementsDashboard;
