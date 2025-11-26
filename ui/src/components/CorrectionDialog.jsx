import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Box,
    Typography,
    TextField,
} from '@mui/material';
import { useForm } from '@tanstack/react-form';

function CorrectionDialog({ open, onClose, onSubmit, isPending }) {
    const form = useForm({
        defaultValues: {
            correctPath: '',
        },
        onSubmit: async ({ value }) => {
            onSubmit(value.correctPath);
        },
    });

    // Reset form when dialog closes
    React.useEffect(() => {
        if (!open) {
            form.reset();
        }
    }, [open, form]);

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>Provide Correct Documentation Path</DialogTitle>
            <DialogContent>
                <form
                    onSubmit={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        form.handleSubmit();
                    }}
                    id="correction-form"
                >
                    <Box sx={{ mt: 2 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                            Help us improve! Please enter the correct documentation path for this
                            error.
                        </Typography>
                        <form.Field
                            name="correctPath"
                            validators={{
                                onChange: ({ value }) =>
                                    !value || value.trim().length === 0
                                        ? 'Please enter the correct documentation path'
                                        : undefined,
                            }}
                        >
                            {(field) => (
                                <TextField
                                    fullWidth
                                    label="Correct Documentation Path"
                                    placeholder="e.g., dataset/docs/services/logitrack/SECURITY_ALERT.md"
                                    value={field.state.value}
                                    onChange={(e) => field.handleChange(e.target.value)}
                                    onBlur={field.handleBlur}
                                    error={field.state.meta.errors.length > 0}
                                    helperText={
                                        field.state.meta.errors[0] ||
                                        'The system will learn from your correction'
                                    }
                                    sx={{ mt: 2 }}
                                />
                            )}
                        </form.Field>
                    </Box>
                </form>
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Cancel</Button>
                <Button
                    type="submit"
                    form="correction-form"
                    variant="contained"
                    color="primary"
                    disabled={isPending}
                >
                    {isPending ? 'Submitting...' : 'Submit Correction'}
                </Button>
            </DialogActions>
        </Dialog>
    );
}

export default CorrectionDialog;
