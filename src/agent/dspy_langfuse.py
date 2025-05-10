from dspy.utils.callback import BaseCallback
from langfuse.decorators import langfuse_context
from langfuse import Langfuse
from litellm import completion_cost
from langfuse.media import LangfuseMedia
from typing import Optional
import dspy

# 1. Define a custom callback class that extends BaseCallback class
class LangFuseDSPYCallback(BaseCallback):
    def __init__(self, signature: dspy.Signature):
        super().__init__()
        self.current_system_prompt = None
        self.current_prompt = None
        self.current_completion = None
        # Initialize Langfuse client
        self.langfuse = Langfuse()
        self.current_span = None

        self.input_field_names = signature.input_fields.keys()
        self.input_field_values = {}

        for input_field_name, input_field in signature.input_fields.items():
            if input_field.annotation == Optional[dspy.Image] or input_field.annotation == dspy.Image:
                pass # TODO: We need to handle this.

    def on_module_start(self, call_id, *args, **kwargs):
        inputs = kwargs.get("inputs")
        extracted_args = inputs["kwargs"]

        for input_field_name in self.input_field_names:
            if input_field_name in extracted_args:
                self.input_field_values[input_field_name] = extracted_args[input_field_name]

    def on_module_end(self, call_id, outputs, exception):
        metadata = {
            "existing_trace_id": langfuse_context.get_current_trace_id(),
            "parent_observation_id": langfuse_context.get_current_observation_id(),
        }
        outputs_extracted = {k:v for k,v in outputs.items()}

        langfuse_context.update_current_observation(
            input=self.input_field_values,
            output=outputs_extracted,
            metadata=metadata
        )

    def on_lm_start(self, call_id, *args, **kwargs):
        # There is a double-trigger, so only count the first trigger.
        if self.current_span:
            return

        # Everything related to the LM instance 
        lm_instance = kwargs.get("instance")
        lm_dict = lm_instance.__dict__
        model_name = lm_dict.get("model")
        temperature = lm_dict.get("kwargs", {}).get("temperature")
        max_tokens = lm_dict.get("kwargs", {}).get("max_tokens")

        # Everything related to the input
        inputs = kwargs.get("inputs")
        messages = inputs.get("messages")

        # Extract prompt from kwargs
        assert messages[0].get("role") == "system"
        system_prompt = messages[0].get("content")
        assert messages[1].get("role") == "user"
        user_input = messages[1].get("content")

        self.current_system_prompt = system_prompt
        self.current_prompt = user_input

        # Create a new generation using the Langfuse client
        trace_id = langfuse_context.get_current_trace_id()
        parent_observation_id = langfuse_context.get_current_observation_id()
        if trace_id:
            self.current_span = self.langfuse.generation(
                input=user_input,
                name=model_name,
                trace_id=trace_id,
                parent_observation_id=parent_observation_id,
                metadata={
                    "model": model_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "system": system_prompt,
                }
            )

    def on_lm_end(self, call_id, outputs, exception):
        if isinstance(outputs, list):
            completion = outputs[0]
            return 
        else:
            model_name = outputs.model
            choices = outputs.choices[0]
            completion = choices.message.content



        total_cost = completion_cost(
            model=model_name,
            prompt=self.current_system_prompt+self.current_prompt,
            completion=completion,
        )

        # End the generation if we have one
        if self.current_span:
            # Use low-level SDK parameters to log usage and cost details
            self.current_span.end(
                output=completion,
                usage_details={
                    "prompt_tokens": len(self.current_system_prompt + self.current_prompt),
                    "completion_tokens": len(completion),
                    "total_tokens": len(self.current_system_prompt + self.current_prompt) + len(completion),
                },
                model=model_name,
                cost_details={
                    "total": total_cost,
                },
            )
            self.current_span = None

        self.current_generation = completion

