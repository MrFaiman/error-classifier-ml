import React, { useState } from 'react';
import {
    Container,
    Paper,
    Box,
    Typography,
    Button,
    Radio,
    RadioGroup,
    FormControlLabel,
    FormControl,
    Card,
    CardContent,
    LinearProgress,
    Alert,
    Chip,
    Grid,
    Divider,
} from '@mui/material';
import { useMutation, useQuery } from '@tanstack/react-query';
import SchoolIcon from '@mui/icons-material/School';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';

function ExamModePage() {
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [selectedAnswer, setSelectedAnswer] = useState('');
    const [answers, setAnswers] = useState([]);
    const [showResults, setShowResults] = useState(false);
    const [quizStarted, setQuizStarted] = useState(false);
    const [numQuestions, setNumQuestions] = useState(10);

    // Fetch quiz questions
    const { data: quizData, refetch: refetchQuiz, isLoading } = useQuery({
        queryKey: ['quiz', numQuestions],
        queryFn: async () => {
            const response = await fetch(`/api/quiz/generate?num_questions=${numQuestions}`);
            if (!response.ok) throw new Error('Failed to fetch quiz');
            return response.json();
        },
        enabled: quizStarted,
    });

    const questions = quizData?.questions || [];
    const currentQuestion = questions[currentQuestionIndex];

    const handleStartQuiz = (num) => {
        setNumQuestions(num);
        setQuizStarted(true);
        setCurrentQuestionIndex(0);
        setAnswers([]);
        setShowResults(false);
        setSelectedAnswer('');
    };

    const handleAnswerSelect = (event) => {
        setSelectedAnswer(event.target.value);
    };

    const handleNextQuestion = () => {
        if (!selectedAnswer) return;

        // Save answer
        const newAnswers = [...answers, {
            question: currentQuestion,
            userAnswer: selectedAnswer,
            isCorrect: selectedAnswer === currentQuestion.correct_answer
        }];
        setAnswers(newAnswers);

        // Move to next question or show results
        if (currentQuestionIndex < questions.length - 1) {
            setCurrentQuestionIndex(currentQuestionIndex + 1);
            setSelectedAnswer('');
        } else {
            setShowResults(true);
        }
    };

    const handleRestart = () => {
        setQuizStarted(false);
        setCurrentQuestionIndex(0);
        setAnswers([]);
        setShowResults(false);
        setSelectedAnswer('');
    };

    const calculateScore = () => {
        const correct = answers.filter(a => a.isCorrect).length;
        const total = answers.length;
        const percentage = (correct / total) * 100;
        return { correct, total, percentage };
    };

    const getGrade = (percentage) => {
        if (percentage >= 90) return { grade: 'A', color: 'success' };
        if (percentage >= 80) return { grade: 'B', color: 'info' };
        if (percentage >= 70) return { grade: 'C', color: 'warning' };
        if (percentage >= 60) return { grade: 'D', color: 'warning' };
        return { grade: 'F', color: 'error' };
    };

    // Start screen
    if (!quizStarted) {
        return (
            <Container maxWidth="md">
                <Box sx={{ mt: 4 }}>
                    <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
                        <SchoolIcon sx={{ fontSize: 80, color: 'primary.main', mb: 2 }} />
                        <Typography variant="h3" gutterBottom>
                            Error Classification Exam
                        </Typography>
                        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                            Test your knowledge of error categories and their associated services.
                            Each question presents an error scenario with four possible classifications.
                        </Typography>

                        <Divider sx={{ my: 3 }} />

                        <Typography variant="h6" gutterBottom>
                            Choose Quiz Length
                        </Typography>
                        <Grid container spacing={3} sx={{ mt: 2 }}>
                            <Grid item xs={12} sm={4}>
                                <Button
                                    variant="outlined"
                                    fullWidth
                                    size="large"
                                    onClick={() => handleStartQuiz(5)}
                                    sx={{
                                        py: 3,
                                        display: 'flex',
                                        flexDirection: 'column',
                                        gap: 0.5,
                                        textTransform: 'none',
                                    }}
                                >
                                    <Typography variant="h6" fontWeight="bold">
                                        Quick Quiz
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        5 Questions
                                    </Typography>
                                </Button>
                            </Grid>
                            <Grid item xs={12} sm={4}>
                                <Button
                                    variant="contained"
                                    fullWidth
                                    size="large"
                                    onClick={() => handleStartQuiz(10)}
                                    sx={{
                                        py: 3,
                                        display: 'flex',
                                        flexDirection: 'column',
                                        gap: 0.5,
                                        textTransform: 'none',
                                    }}
                                >
                                    <Typography variant="h6" fontWeight="bold">
                                        Standard Exam
                                    </Typography>
                                    <Typography variant="caption">
                                        10 Questions
                                    </Typography>
                                </Button>
                            </Grid>
                            <Grid item xs={12} sm={4}>
                                <Button
                                    variant="outlined"
                                    fullWidth
                                    size="large"
                                    onClick={() => handleStartQuiz(20)}
                                    sx={{
                                        py: 3,
                                        display: 'flex',
                                        flexDirection: 'column',
                                        gap: 0.5,
                                        textTransform: 'none',
                                    }}
                                >
                                    <Typography variant="h6" fontWeight="bold">
                                        Full Exam
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        20 Questions
                                    </Typography>
                                </Button>
                            </Grid>
                        </Grid>
                    </Paper>
                </Box>
            </Container>
        );
    }

    // Loading screen
    if (isLoading) {
        return (
            <Container maxWidth="md">
                <Box sx={{ mt: 4 }}>
                    <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
                        <Typography variant="h6" gutterBottom>
                            Generating Quiz Questions...
                        </Typography>
                        <LinearProgress sx={{ mt: 2 }} />
                    </Paper>
                </Box>
            </Container>
        );
    }

    // Results screen
    if (showResults) {
        const score = calculateScore();
        const gradeInfo = getGrade(score.percentage);

        return (
            <Container maxWidth="md">
                <Box sx={{ mt: 4 }}>
                    <Paper elevation={3} sx={{ p: 4 }}>
                        <Typography variant="h4" gutterBottom align="center">
                            Exam Results
                        </Typography>

                        <Box sx={{ textAlign: 'center', my: 4 }}>
                            <Chip
                                label={`Grade: ${gradeInfo.grade}`}
                                color={gradeInfo.color}
                                sx={{ fontSize: '2rem', p: 3, mb: 2 }}
                            />
                            <Typography variant="h5">
                                Score: {score.correct} / {score.total} ({score.percentage.toFixed(1)}%)
                            </Typography>
                        </Box>

                        <Divider sx={{ my: 3 }} />

                        <Typography variant="h6" gutterBottom>
                            Question Review
                        </Typography>

                        {answers.map((answer, index) => (
                            <Card key={index} sx={{ mb: 2 }}>
                                <CardContent>
                                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                        {answer.isCorrect ? (
                                            <CheckCircleIcon color="success" sx={{ mr: 1 }} />
                                        ) : (
                                            <CancelIcon color="error" sx={{ mr: 1 }} />
                                        )}
                                        <Typography variant="subtitle1" fontWeight="medium">
                                            Question {index + 1}
                                        </Typography>
                                    </Box>

                                    <Typography variant="body2" sx={{ mb: 2, whiteSpace: 'pre-line' }}>
                                        {answer.question.question}
                                    </Typography>

                                    <Box sx={{ mb: 1 }}>
                                        <Typography variant="caption" color="text.secondary">
                                            Your answer:
                                        </Typography>
                                        <Typography
                                            variant="body2"
                                            color={answer.isCorrect ? 'success.main' : 'error.main'}
                                        >
                                            {answer.userAnswer}: {answer.question.options[answer.userAnswer]}
                                        </Typography>
                                    </Box>

                                    {!answer.isCorrect && (
                                        <Box sx={{ mb: 1 }}>
                                            <Typography variant="caption" color="text.secondary">
                                                Correct answer:
                                            </Typography>
                                            <Typography variant="body2" color="success.main">
                                                {answer.question.correct_answer}:{' '}
                                                {answer.question.options[answer.question.correct_answer]}
                                            </Typography>
                                        </Box>
                                    )}

                                    <Alert severity="info" sx={{ mt: 2 }}>
                                        {answer.question.explanation}
                                    </Alert>
                                </CardContent>
                            </Card>
                        ))}

                        <Box sx={{ textAlign: 'center', mt: 4 }}>
                            <Button
                                variant="contained"
                                size="large"
                                startIcon={<RestartAltIcon />}
                                onClick={handleRestart}
                            >
                                Take Another Exam
                            </Button>
                        </Box>
                    </Paper>
                </Box>
            </Container>
        );
    }

    // Question screen
    return (
        <Container maxWidth="md">
            <Box sx={{ mt: 4 }}>
                <Paper elevation={3} sx={{ p: 4 }}>
                    {/* Progress bar */}
                    <Box sx={{ mb: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                                Question {currentQuestionIndex + 1} of {questions.length}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                {Math.round(((currentQuestionIndex + 1) / questions.length) * 100)}%
                            </Typography>
                        </Box>
                        <LinearProgress
                            variant="determinate"
                            value={((currentQuestionIndex + 1) / questions.length) * 100}
                        />
                    </Box>

                    {/* Question */}
                    <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
                        {currentQuestion?.question}
                    </Typography>

                    {/* Answer options */}
                    <FormControl component="fieldset" fullWidth>
                        <RadioGroup value={selectedAnswer} onChange={handleAnswerSelect}>
                            {['A', 'B', 'C', 'D'].map((letter) => (
                                <Card
                                    key={letter}
                                    variant="outlined"
                                    sx={{
                                        mb: 2,
                                        cursor: 'pointer',
                                        border: selectedAnswer === letter ? 2 : 1,
                                        borderColor:
                                            selectedAnswer === letter ? 'primary.main' : 'divider',
                                        '&:hover': {
                                            borderColor: 'primary.light',
                                            bgcolor: 'action.hover',
                                        },
                                    }}
                                    onClick={() => setSelectedAnswer(letter)}
                                >
                                    <CardContent>
                                        <FormControlLabel
                                            value={letter}
                                            control={<Radio />}
                                            label={
                                                <Typography variant="body1">
                                                    <strong>{letter}.</strong>{' '}
                                                    {currentQuestion?.options[letter]}
                                                </Typography>
                                            }
                                            sx={{ width: '100%', m: 0 }}
                                        />
                                    </CardContent>
                                </Card>
                            ))}
                        </RadioGroup>
                    </FormControl>

                    {/* Navigation buttons */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
                        <Button variant="outlined" onClick={handleRestart}>
                            Exit Exam
                        </Button>
                        <Button
                            variant="contained"
                            size="large"
                            endIcon={<NavigateNextIcon />}
                            onClick={handleNextQuestion}
                            disabled={!selectedAnswer}
                        >
                            {currentQuestionIndex < questions.length - 1
                                ? 'Next Question'
                                : 'Submit Exam'}
                        </Button>
                    </Box>
                </Paper>
            </Box>
        </Container>
    );
}

export default ExamModePage;
